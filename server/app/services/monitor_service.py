# server/app/services/monitor_service.py
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from ..db.models.printer import Printer
from ..db.models.printer_oids import PrinterOIDs
from ..schemas.printer import PrinterCreate, PrinterUpdate
from .snmp_service import SNMPService

logger = logging.getLogger(__name__)

class MonitorService:
    def __init__(self, db: Session):
        self.db = db
        self.snmp_service = SNMPService()

    async def get_monitored_printers(self, skip: int = 0, limit: int = 100):
        """Obtiene lista de impresoras monitoreadas."""
        try:
            logger.debug(f"Obteniendo impresoras monitoreadas - skip: {skip}, limit: {limit}")
            return self.db.query(Printer).filter(Printer.is_active == True).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error obteniendo impresoras monitoreadas: {str(e)}")
            raise

    async def get_monitor_data(self, printer_id: int):
        """Obtiene datos de monitoreo de una impresora específica."""
        try:
            logger.debug(f"Buscando datos de monitoreo para impresora {printer_id}")
            printer = self.db.query(Printer).filter(Printer.id == printer_id).first()
            if not printer:
                raise ValueError("Impresora no encontrada")
            return {
                "printer": printer.to_dict(),
                "counters": printer.counters,
                "supplies": printer.supplies,
                "status": printer.status,
                "last_check": printer.last_check,
                "alerts": printer.check_alerts()
            }
        except Exception as e:
            logger.error(f"Error obteniendo datos de monitoreo para impresora {printer_id}: {str(e)}")
            raise

    async def scan_printer(self, printer_id: int):
        """Realiza un escaneo SNMP de la impresora."""
        try:
            logger.info(f"Iniciando escaneo de impresora {printer_id}")
            printer = self.db.query(Printer).filter(Printer.id == printer_id).first()
            if not printer:
                raise ValueError("Impresora no encontrada")

            oid_config = printer.oid_config
            if not oid_config:
                raise ValueError("Configuración OID no encontrada")

            # Realizar consultas SNMP
            snmp_data = await self.snmp_service.get_printer_data(
                ip=printer.ip_address,
                community=printer.snmp_community,
                version=printer.snmp_version,
                port=printer.snmp_port,
                oids=oid_config.get_supported_oids()
            )

            # Actualizar datos de monitoreo
            updated_data = self._process_snmp_data(printer, snmp_data)
            self.db.commit()

            logger.info(f"Escaneo de impresora {printer_id} completado")
            return updated_data

        except Exception as e:
            logger.error(f"Error en escaneo de impresora {printer_id}: {str(e)}")
            self._handle_scan_error(printer)
            raise

    def _process_snmp_data(self, printer, snmp_data):
        """Procesa y actualiza los datos recibidos vía SNMP."""
        try:
            # Actualizar valores últimos
            printer.last_values = snmp_data
            printer.last_check = datetime.utcnow().isoformat()
            
            # Actualizar contadores
            if 'counters' in snmp_data:
                for counter_type, value in snmp_data['counters'].items():
                    printer.update_counter(counter_type, value)
            
            # Actualizar suministros
            if 'supplies' in snmp_data:
                for supply_type, data in snmp_data['supplies'].items():
                    printer.update_supply(
                        supply_type=supply_type,
                        value=data.get('level'),
                        max_value=data.get('max'),
                        supply_identifier=data.get('type')
                    )

            # Actualizar estado
            old_status = printer.status
            new_status = self.snmp_service.determine_status(snmp_data)
            if old_status != new_status:
                printer.status = new_status
                printer.update_history('status_changes', {
                    'old_status': old_status,
                    'new_status': new_status,
                    'timestamp': datetime.utcnow().isoformat()
                })

            # Resetear contador de errores
            printer.consecutive_failures = 0
            
            return printer.to_dict()

        except Exception as e:
            logger.error(f"Error procesando datos SNMP: {str(e)}")
            raise

    def _handle_scan_error(self, printer):
        """Maneja errores durante el escaneo."""
        try:
            if printer:
                printer.consecutive_failures += 1
                if printer.consecutive_failures >= 3:
                    printer.status = 'error'
                    printer.update_history('errors', {
                        'type': 'scan_failure',
                        'consecutive_failures': printer.consecutive_failures,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                self.db.commit()
        except Exception as e:
            logger.error(f"Error manejando fallo de escaneo: {str(e)}")

    async def get_monitor_history(self, printer_id: int, event_type: str = None):
        """Obtiene historial de monitoreo de una impresora."""
        try:
            printer = self.db.query(Printer).filter(Printer.id == printer_id).first()
            if not printer:
                raise ValueError("Impresora no encontrada")
            
            history = printer.history
            if event_type and event_type in history:
                return {event_type: history[event_type]}
            return history

        except Exception as e:
            logger.error(f"Error obteniendo historial de monitoreo: {str(e)}")
            raise

    async def update_monitor_settings(self, printer_id: int, settings: dict):
        """Actualiza configuración de monitoreo de una impresora."""
        try:
            printer = self.db.query(Printer).filter(Printer.id == printer_id).first()
            if not printer:
                raise ValueError("Impresora no encontrada")

            # Actualizar configuración existente
            current_settings = printer.settings
            current_settings.update(settings)
            printer.settings = current_settings
            
            self.db.commit()
            logger.info(f"Configuración de monitoreo actualizada para impresora {printer_id}")
            return printer.settings

        except Exception as e:
            logger.error(f"Error actualizando configuración de monitoreo: {str(e)}")
            self.db.rollback()
            raise