# server/app/db/models/printer_oids.py
from app.db.base import BaseModel
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

class PrinterOIDs(BaseModel):
    __tablename__ = 'printer_oids'
    
    # Información básica
    brand = Column(String, nullable=False)  # Konica Minolta, HP, Epson, etc.
    model_family = Column(String, nullable=False)  # Familia de modelos específica
    description = Column(String)
    
    # OIDs para contadores de páginas
    oid_total_pages = Column(String)
    oid_total_color_pages = Column(String)
    oid_total_bw_pages = Column(String)
    oid_total_copies = Column(String)
    oid_total_prints = Column(String)
    oid_total_scans = Column(String)
    oid_duplex_pages = Column(String)
    oid_total_faxes = Column(String)
    
    # OIDs para tamaños de papel
    oid_a4_pages = Column(String)
    oid_a3_pages = Column(String)
    oid_letter_pages = Column(String)
    oid_legal_pages = Column(String)
    
    # OIDs para niveles de tóner
    oid_black_toner_level = Column(String)
    oid_cyan_toner_level = Column(String)
    oid_magenta_toner_level = Column(String)
    oid_yellow_toner_level = Column(String)
    
    # OIDs para capacidad máxima de tóner
    oid_black_toner_max = Column(String)
    oid_cyan_toner_max = Column(String)
    oid_magenta_toner_max = Column(String)
    oid_yellow_toner_max = Column(String)
    
    # OIDs para estado de tóner
    oid_black_toner_status = Column(String)
    oid_cyan_toner_status = Column(String)
    oid_magenta_toner_status = Column(String)
    oid_yellow_toner_status = Column(String)
    
    # OIDs para unidades de imagen/drums
    oid_black_drum_level = Column(String)
    oid_cyan_drum_level = Column(String)
    oid_magenta_drum_level = Column(String)
    oid_yellow_drum_level = Column(String)
    
    # OIDs para otros consumibles
    oid_fuser_unit_level = Column(String)
    oid_transfer_belt_level = Column(String)
    oid_waste_toner_level = Column(String)
    oid_waste_toner_max = Column(String)
    
    # OIDs para bandejas de papel
    oid_tray1_level = Column(String)
    oid_tray1_max_capacity = Column(String)
    oid_tray1_status = Column(String)
    oid_tray1_paper_size = Column(String)
    oid_tray1_paper_type = Column(String)
    
    oid_tray2_level = Column(String)
    oid_tray2_max_capacity = Column(String)
    oid_tray2_status = Column(String)
    oid_tray2_paper_size = Column(String)
    oid_tray2_paper_type = Column(String)
    
    oid_tray3_level = Column(String)
    oid_tray3_max_capacity = Column(String)
    oid_tray3_status = Column(String)
    oid_tray3_paper_size = Column(String)
    oid_tray3_paper_type = Column(String)
    
    oid_bypass_tray_level = Column(String)
    oid_bypass_tray_status = Column(String)
    
    # OIDs para información del sistema
    oid_printer_status = Column(String)
    oid_printer_model = Column(String)
    oid_serial_number = Column(String)
    oid_firmware_version = Column(String)
    oid_system_contact = Column(String)
    oid_system_name = Column(String)
    oid_system_location = Column(String)
    oid_printer_memory = Column(String)
    oid_temperature = Column(String)
    oid_display_message = Column(String)
    
    # OIDs para errores y alertas
    oid_error_messages = Column(String)
    oid_warning_messages = Column(String)
    oid_service_messages = Column(String)
    
    # OIDs para información de red
    oid_ip_address = Column(String)
    oid_mac_address = Column(String)
    oid_subnet_mask = Column(String)
    oid_gateway = Column(String)
    
    # Relación con las impresoras
    printers = relationship("Printer", back_populates="oid_config")
    
    class Meta:
        unique_together = (('brand', 'model_family'),)
    
    def to_dict(self):
        """Convierte el objeto a diccionario para serialización."""
        return {
            "id": self.id,
            "brand": self.brand,
            "model_family": self.model_family,
            "description": self.description,
            # OIDs básicos (para compatibilidad con código existente)
            "oid_total_pages": self.oid_total_pages,
            "oid_total_color_pages": self.oid_total_color_pages,
            "oid_total_bw_pages": self.oid_total_bw_pages,
            "oid_black_toner_level": self.oid_black_toner_level,
            "oid_cyan_toner_level": self.oid_cyan_toner_level,
            "oid_magenta_toner_level": self.oid_magenta_toner_level,
            "oid_yellow_toner_level": self.oid_yellow_toner_level,
            # OIDs de sistema (modelo y serie)
            "oid_printer_model": self.oid_printer_model,
            "oid_serial_number": self.oid_serial_number,
            # Estructura completa organizada
            "oids": {
                "system": {
                    "model": self.oid_printer_model,
                    "serial": self.oid_serial_number,
                    "status": self.oid_printer_status,
                    "firmware": self.oid_firmware_version,
                    "memory": self.oid_printer_memory,
                    "temperature": self.oid_temperature,
                    "display": self.oid_display_message
                },
                "counters": {
                    "total_pages": self.oid_total_pages,
                    "total_color_pages": self.oid_total_color_pages,
                    "total_bw_pages": self.oid_total_bw_pages,
                    "total_copies": self.oid_total_copies,
                    "total_prints": self.oid_total_prints,
                    "total_scans": self.oid_total_scans,
                    "duplex_pages": self.oid_duplex_pages,
                    "total_faxes": self.oid_total_faxes
                },
                "toner_levels": {
                    "black": self.oid_black_toner_level,
                    "cyan": self.oid_cyan_toner_level,
                    "magenta": self.oid_magenta_toner_level,
                    "yellow": self.oid_yellow_toner_level
                },
                "toner_max": {
                    "black": self.oid_black_toner_max,
                    "cyan": self.oid_cyan_toner_max,
                    "magenta": self.oid_magenta_toner_max,
                    "yellow": self.oid_yellow_toner_max
                },
                "network": {
                    "ip": self.oid_ip_address,
                    "mac": self.oid_mac_address,
                    "subnet": self.oid_subnet_mask,
                    "gateway": self.oid_gateway
                }
            }
        }
        
    def get_oid_by_name(self, oid_name):
        """
        Obtiene el valor de un OID específico por el nombre del atributo.
        
        :param oid_name: Nombre del atributo OID (ej: 'oid_black_toner_level')
        :return: Valor del OID o None si no existe
        """
        return getattr(self, oid_name, None)