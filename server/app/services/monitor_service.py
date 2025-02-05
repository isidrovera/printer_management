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

    def update_printer_data(self, agent_id: int, printer_data: Dict[str, Any]) -> Printer:
        """
        Actualiza los datos de una impresora para un agente específico.
        Si la impresora no existe, la crea.
        
        Args:
            agent_id (int): ID del agente
            printer_data (Dict[str, Any]): Datos de la impresora
            
        Returns:
            Printer: Objeto impresora actualizado o creado
            
        Raises:
            ValueError: Si faltan datos requeridos
            Exception: Para otros errores durante el proceso
        """
        try:
            logger.info(f"Iniciando creación/actualización de impresora con datos: {printer_data}")

            if not printer_data:
                logger.error("No se proporcionaron datos de la impresora")
                raise ValueError("No se proporcionaron datos de la impresora")

            # Validar campos requeridos
            required_fields = ["name", "brand", "model", "ip_address"]
            for field in required_fields:
                if field not in printer_data:
                    logger.error(f"Campo requerido faltante: {field}")
                    raise ValueError(f"El campo {field} es requerido")

            # Buscar la impresora existente por IP
            printer = self.db.query(Printer).filter(
                Printer.ip_address == printer_data["ip_address"]
            ).first()

            logger.info(f"Impresora existente encontrada: {printer is not None}")

            if not printer:
                logger.info("Creando nueva impresora")
                printer = Printer(
                    name=printer_data["name"],
                    brand=printer_data["brand"],
                    model=printer_data["model"],
                    ip_address=printer_data["ip_address"],
                    agent_id=agent_id,
                    status=printer_data.get("status", "offline"),
                    last_check=datetime.utcnow(),
                    oid_config_id=1  # ID por defecto para PrinterOIDs
                )

                # Asignar cliente si se proporciona
                if printer_data.get("client_id"):
                    printer.client_id = int(printer_data["client_id"])
                    logger.info(f"Cliente asignado a la nueva impresora: {printer_data['client_id']}")

                self.db.add(printer)

                # Estructura de datos predeterminada para nueva impresora
                printer.printer_data = {
                    "counters": {
                        "total": 0,
                        "color": {
                            "total": 0,
                            "cyan": 0,
                            "magenta": 0,
                            "yellow": 0,
                            "black": 0
                        },
                        "black_white": 0
                    },
                    "supplies": {
                        "toners": {
                            "black": {
                                "current_level": 100,
                                "max_level": 100,
                                "percentage": 100,
                                "status": "ok"
                            },
                            "cyan": {
                                "current_level": 100,
                                "max_level": 100,
                                "percentage": 100,
                                "status": "ok"
                            },
                            "magenta": {
                                "current_level": 100,
                                "max_level": 100,
                                "percentage": 100,
                                "status": "ok"
                            },
                            "yellow": {
                                "current_level": 100,
                                "max_level": 100,
                                "percentage": 100,
                                "status": "ok"
                            }
                        }
                    }
                }

            else:
                # Actualizar datos de impresora existente
                printer.name = printer_data["name"]
                printer.brand = printer_data["brand"]
                printer.model = printer_data["model"]
                printer.status = printer_data.get("status", "offline")
                printer.last_check = datetime.utcnow()

                # Actualizar cliente si se proporciona
                if printer_data.get("client_id"):
                    printer.client_id = int(printer_data["client_id"])
                    logger.info(f"Cliente actualizado para la impresora: {printer_data['client_id']}")

            # Confirmar cambios en la base de datos
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