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
        
        :param agent_id: ID del agente que reporta los datos
        :param printer_data: Diccionario con los datos de la impresora
        :return: Instancia de Printer actualizada
        """
        try:
            # Buscar la impresora por IP o número de serie
            printer = self.db.query(Printer).filter(
                (Printer.ip_address == printer_data.get('ip_address')) | 
                (Printer.serial_number == printer_data.get('serial_number'))
            ).first()

            # Si no existe, crear una nueva
            if not printer:
                printer = Printer(
                    name=printer_data.get('name', 'Unnamed Printer'),
                    model=printer_data.get('model'),
                    brand=printer_data.get('brand'),
                    serial_number=printer_data.get('serial_number'),
                    ip_address=printer_data.get('ip_address'),
                    agent_id=agent_id
                )
                self.db.add(printer)

            # Actualizar datos de la impresora
            printer.update_printer_data(printer_data)
            
            # Confirmar cambios
            self.db.commit()
            self.db.refresh(printer)

            return printer

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating printer data: {str(e)}")
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