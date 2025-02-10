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

    def update_printer_data(self, printer_data: Dict[str, Any], agent_id: int = None) -> Printer:
        """
        Actualiza los datos de una impresora preservando valores cuando el agente está desconectado.
        """
        try:
            logger.info(f"Iniciando actualización de impresora con datos: {printer_data}")

            if not printer_data:
                logger.error("No se proporcionaron datos de la impresora")
                raise ValueError("No se proporcionaron datos de la impresora")

            # Validar campos requeridos
            required_fields = ["name", "brand", "model", "ip_address"]
            for field in required_fields:
                if not printer_data.get(field):
                    logger.error(f"Campo requerido faltante: {field}")
                    raise ValueError(f"El campo {field} es requerido")

            # Buscar la impresora existente por IP
            printer = self.db.query(Printer).filter(
                Printer.ip_address == printer_data["ip_address"]
            ).first()

            if not printer:
                logger.info("Creando nueva impresora")
                printer = Printer(
                    name=printer_data["name"],
                    brand=printer_data["brand"],
                    model=printer_data["model"],
                    ip_address=printer_data["ip_address"],
                    agent_id=agent_id,
                    status='online',
                    last_check=datetime.utcnow(),
                    oid_config_id=1,
                    printer_data={}
                )
                self.db.add(printer)
            else:
                # Actualizar datos básicos
                printer.name = printer_data["name"]
                printer.brand = printer_data["brand"]
                printer.model = printer_data["model"]
                printer.last_check = datetime.utcnow()
                
                if agent_id is not None:
                    printer.agent_id = agent_id

            # Actualizar client_id si se proporciona
            if printer_data.get("client_id"):
                printer.client_id = int(printer_data["client_id"])

            # Manejar printer_data
            if "printer_data" in printer_data:
                current_data = printer.printer_data or {}
                new_data = printer_data["printer_data"]
                
                # Actualizar contadores
                if "counters" in new_data:
                    current_counters = current_data.get("counters", {})
                    new_counters = new_data["counters"]
                    
                    for key in ["total_pages", "color_pages", "bw_pages"]:
                        new_value = new_counters.get(key)
                        if new_value not in [None, 0]:
                            current_counters[key] = new_value
                        elif key not in current_counters:
                            current_counters[key] = 0
                    
                    current_data["counters"] = current_counters

                # Actualizar suministros
                if "supplies" in new_data:
                    current_supplies = current_data.get("supplies", {})
                    new_supplies = new_data["supplies"]
                    
                    for supply_type in ["toners", "drums"]:
                        if supply_type in new_supplies:
                            current_type = current_supplies.get(supply_type, {})
                            new_type = new_supplies[supply_type]
                            
                            for color in ["black", "cyan", "magenta", "yellow"]:
                                if color in new_type:
                                    current_color = current_type.get(color, {})
                                    new_color = new_type[color]
                                    
                                    # Solo actualizar si los nuevos valores son válidos
                                    if isinstance(new_color, dict):
                                        for key in ["level", "max", "percentage"]:
                                            if key in new_color and new_color[key] not in [None, 0]:
                                                current_color[key] = new_color[key]
                                            elif key not in current_color:
                                                current_color[key] = 100 if key == "percentage" else 0
                                                
                                    current_type[color] = current_color
                            
                            current_supplies[supply_type] = current_type
                    
                    current_data["supplies"] = current_supplies

                # Actualizar el estado solo si no es None
                if new_data.get("status") is not None:
                    current_data["status"] = new_data["status"]
                    printer.status = new_data["status"]
                elif printer_data.get("status") is not None:
                    printer.status = printer_data["status"]
                else:
                    printer.status = 'online'

                printer.printer_data = current_data

            self.db.commit()
            self.db.refresh(printer)
            
            logger.info(f"Impresora actualizada exitosamente. ID: {printer.id}, IP: {printer.ip_address}")
            return printer

        except Exception as e:
            logger.error(f"Error en update_printer_data: {str(e)}")
            self.db.rollback()
            raise

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
    async def get_count(self) -> int:
        """
        Obtiene el número total de impresoras.
        """
        try:
            count = self.db.query(Printer).count()
            logger.info(f"Total de impresoras encontradas: {count}")
            return count
        except Exception as e:
            logger.error(f"Error obteniendo conteo de impresoras: {str(e)}")
            return 0

    async def get_count_by_status(self, status: str) -> int:
        """
        Obtiene el número de impresoras por estado específico.
        """
        try:
            count = self.db.query(Printer).filter(Printer.status == status).count()
            logger.info(f"Total de impresoras con estado {status}: {count}")
            return count
        except Exception as e:
            logger.error(f"Error obteniendo conteo de impresoras por estado: {str(e)}")
            return 0

    async def get_all(self):
        """
        Obtiene todas las impresoras.
        """
        try:
            printers = self.db.query(Printer).all()
            logger.info(f"Total de impresoras recuperadas: {len(printers)}")
            return printers
        except Exception as e:
            logger.error(f"Error obteniendo todas las impresoras: {str(e)}")
            return []