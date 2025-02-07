# server/app/services/monitor_service.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models.printer import Printer
from app.db.models.agent import Agent
from datetime import datetime, timedelta
from app.core.logging import logger

class PrinterMonitorService:
    def __init__(self, db: Session):
        self.db = db

    async def update_printer_data(self, ip: str, data: Dict[str, Any]) -> bool:
        """
        Envía datos actualizados al servidor.
        
        Args:
            ip (str): IP de la impresora
            data (Dict[str, Any]): Datos a actualizar
            
        Returns:
            bool: True si la actualización fue exitosa
        """
        try:
            logger.info(f"Preparando actualización de datos para {ip}")
            
            # Obtener los datos de la impresora del servidor
            printers = await self.get_monitored_printers()
            printer_info = next((p for p in printers if p['ip_address'] == ip), None)
            
            if not printer_info:
                logger.error(f"No se encontró información de la impresora {ip} en el servidor")
                return False
            
            # Convertir todos los valores SNMP
            processed_data = self._convert_nested_snmp_values(data)
            
            # Preparar los datos según el formato requerido por el servidor
            update_data = {
                'ip_address': ip,
                'name': printer_info.get('name'),
                'brand': printer_info.get('brand'),
                'model': printer_info.get('model'),
                'client_id': printer_info.get('client_id'),
                'status': processed_data.get('status', 'offline'),
                'oid_config_id': 1,  # Valor por defecto
                'last_check': datetime.utcnow().isoformat(),
                'agent_id': self._get_agent_id()
            }
            
            # Agregar datos de monitoreo
            if processed_data.get('counters'):
                update_data['printer_data'] = {
                    'counters': {
                        'total': processed_data['counters'].get('total_pages', 0),
                        'color': {
                            'total': processed_data['counters'].get('color_pages', 0),
                            'black': 0,
                            'cyan': 0,
                            'magenta': 0,
                            'yellow': 0
                        },
                        'black_white': processed_data['counters'].get('bw_pages', 0)
                    }
                }
            
            if processed_data.get('supplies', {}).get('toners'):
                if 'printer_data' not in update_data:
                    update_data['printer_data'] = {}
                
                update_data['printer_data']['supplies'] = {
                    'toners': {
                        color: {
                            'current_level': toner.get('level', 100),
                            'max_level': toner.get('max', 100),
                            'percentage': min(100, int((toner.get('level', 100) / toner.get('max', 100)) * 100)),
                            'status': 'ok'
                        }
                        for color, toner in processed_data['supplies']['toners'].items()
                    }
                }
            
            # Validar serialización antes de enviar
            try:
                json.dumps(update_data)
            except Exception as e:
                logger.error(f"Error de serialización para {ip}: {str(e)}")
                return False
            
            async with aiohttp.ClientSession() as session:
                base_url = self.server_url.replace('ws://', 'http://')
                url = f"{base_url}/api/v1/monitor/printers/update"
                
                headers = {
                    "Authorization": f"Bearer {settings.AGENT_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                # Parámetros de consulta requeridos - quitamos el self
                params = {
                    'agent_id': str(self._get_agent_id())
                }
                
                logger.debug(f"Enviando datos a {url}")
                logger.debug(f"Headers: {headers}")
                logger.debug(f"Parámetros: {params}")
                logger.debug(f"Datos: {json.dumps(update_data, indent=2)}")
                
                async with session.post(
                    url, 
                    json=update_data, 
                    headers=headers,
                    params=params
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        logger.info(f"Datos actualizados exitosamente para {ip}")
                        return True
                    else:
                        logger.error(f"Error actualizando datos para {ip}")
                        logger.error(f"Status: {response.status}")
                        logger.error(f"Respuesta: {response_text}")
                        return False
                        
        except aiohttp.ClientError as e:
            logger.error(f"Error de conexión actualizando {ip}: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error inesperado actualizando {ip}: {str(e)}", exc_info=True)
            return False

    def get_printers_by_agent(self, agent_id: int) -> List[Printer]:
        """
        Obtiene todas las impresoras asociadas a un agente.
        
        :param agent_id: ID del agente
        :return: Lista de impresoras del agente
        """
        return self.db.query(Printer).filter(Printer.agent_id == agent_id).all()

    def get_printers_with_critical_supplies(self) -> List[Printer]:
        """
        Obtiene impresoras con consumibles en estado crítico.
        
        :return: Lista de impresoras con consumibles críticos
        """
        # Filtrar impresoras con consumibles críticos
        printers = self.db.query(Printer).all()
        return [
            printer for printer in printers 
            if printer.check_critical_supplies()
        ]

    def get_printer_history(self, printer_id: int, days: int = 7) -> Dict[str, List]:
        """
        Obtiene el historial de una impresora en un rango de días.
        
        :param printer_id: ID de la impresora
        :param days: Número de días de histórico a recuperar
        :return: Diccionario con históricos de la impresora
        """
        printer = self.db.query(Printer).get(printer_id)
        if not printer:
            return {}

        # Filtrar históricos por fecha
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        filtered_history = {
            key: [
                entry for entry in printer.data_history.get(key, [])
                if datetime.fromisoformat(entry['timestamp']) >= cutoff_date
            ]
            for key in printer.data_history.keys()
        }

        return filtered_history

    def generate_printer_report(self, agent_id: int = None) -> Dict[str, Any]:
        """
        Genera un informe general de impresoras.
        
        :param agent_id: Opcional, filtrar por agente
        :return: Diccionario con resumen de impresoras
        """
        query = self.db.query(Printer)
        if agent_id:
            query = query.filter(Printer.agent_id == agent_id)

        printers = query.all()

        report = {
            'total_printers': len(printers),
            'printers_by_status': {},
            'printers_by_brand': {},
            'critical_supplies': []
        }

        # Conteo por estado y marca
        for printer in printers:
            # Conteo por estado
            report['printers_by_status'][printer.status] = \
                report['printers_by_status'].get(printer.status, 0) + 1

            # Conteo por marca
            report['printers_by_brand'][printer.brand] = \
                report['printers_by_brand'].get(printer.brand, 0) + 1

            # Consumibles críticos
            critical_supplies = printer.check_critical_supplies()
            if critical_supplies:
                report['critical_supplies'].append({
                    'printer_id': printer.id,
                    'printer_name': printer.name,
                    'critical_supplies': critical_supplies
                })

        return report

    def get_critical_printers(self) -> List[Printer]:
        """
        Obtiene todas las impresoras que requieren atención.
        Incluye impresoras con errores o con consumibles críticos.
        
        :return: Lista de impresoras críticas
        """
        printers = self.db.query(Printer).all()
        critical_printers = []
        
        for printer in printers:
            # Incluir impresoras con error
            if printer.status == 'error':
                critical_printers.append(printer)
                continue
                
            # Incluir impresoras con consumibles críticos
            if printer.check_critical_supplies():
                critical_printers.append(printer)
                
        return critical_printers