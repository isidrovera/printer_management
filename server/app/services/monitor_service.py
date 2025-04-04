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
        Actualiza los datos de una impresora.
        
        Args:
            printer_data (Dict[str, Any]): Datos de la impresora
            agent_id (int, optional): ID del agente que envía los datos
            
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
                    status=printer_data.get("status", "offline"),
                    last_check=datetime.utcnow(),
                    oid_config_id=1  # ID por defecto para PrinterOIDs
                )

                # Asignar cliente si se proporciona
                if printer_data.get("client_id"):
                    printer.client_id = int(printer_data["client_id"])
                    logger.info(f"Cliente asignado a la nueva impresora: {printer_data['client_id']}")

                self.db.add(printer)

            else:
                # Actualizar datos básicos de impresora existente
                printer.name = printer_data["name"]
                printer.brand = printer_data["brand"]
                printer.model = printer_data["model"]
                printer.status = printer_data.get("status", "offline")
                printer.last_check = datetime.utcnow()

                # Actualizar agent_id si se proporciona
                if agent_id is not None:
                    printer.agent_id = agent_id
                # Actualizar número de serie si está presente en los datos
                if "serial_number" in printer_data:
                    printer.serial_number = printer_data["serial_number"]
                # Actualizar cliente si se proporciona
                if printer_data.get("client_id"):
                    printer.client_id = int(printer_data["client_id"])

                # Actualizar datos de monitoreo si están presentes
                if printer_data.get("printer_data"):
                    printer.printer_data = printer_data["printer_data"]

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
    

    def get_count(self) -> int:
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

    def get_count_by_status(self, status: str) -> int:
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

    def get_all(self):
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

    def count_by_status(self) -> Dict[str, int]:
        """
        Obtiene un conteo de impresoras por estado.
        """
        try:
            statuses = ['online', 'offline', 'error']
            counts = {status: 0 for status in statuses}
            counts['total'] = 0
            
            printers = self.get_all()
            counts['total'] = len(printers)
            
            for printer in printers:
                if printer.status in statuses:
                    counts[printer.status] += 1
            
            return counts
        except Exception as e:
            logger.error(f"Error contando impresoras por estado: {str(e)}")
            return {
                "total": 0,
                "online": 0,
                "offline": 0,
                "error": 0
            }