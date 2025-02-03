# server/app/db/models/printer_oids.py
from app.db.base import BaseModel
from sqlalchemy import Column, String, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship

class PrinterOIDs(BaseModel):
    __tablename__ = 'printer_oids'
    
    brand = Column(String, nullable=False)
    model = Column(String)  # Null si aplica a toda la marca
    
    # OIDs específicos por marca/modelo
    oids = Column(JSON, default={
        'system': {
            'description': None,
            'name': None,
            'uptime': None,
            'serial': None,
            'model': None
        },
        'status': {
            'general': None,
            'display': None,
            'error': None
        },
        'supplies': {
            'black': None,
            'cyan': None,
            'magenta': None,
            'yellow': None,
            'waste': None,
            'drum': None,
            'fuser': None,
            'maintenance_kit': None,
            'max_capacity': None
        },
        'counters': {
            'total': None,
            'black': None,
            'color': None,
            'duplex': None,
            'scan': None,
            'copy': None,
            'fax': None
        },
        'paper': {
            'tray1_status': None,
            'tray2_status': None,
            'tray3_status': None,
            'tray1_size': None,
            'tray2_size': None,
            'tray3_size': None
        }
    })
    
    # Configuración SNMP específica
    snmp_config = Column(JSON, default={
        'version': '2c',
        'community': 'public',
        'port': 161,
        'timeout': 2,
        'retries': 3
    })
    
    # Mapeos de valores específicos de la marca
    value_mappings = Column(JSON, default={
        'status': {},
        'errors': {},
        'paper_sizes': {},
        'supply_types': {}
    })
    
    # Relaciones
    printers = relationship("Printer", back_populates="oid_config")
    
    def get_oid(self, category, subcategory):
        """Obtiene un OID específico."""
        try:
            return self.oids[category][subcategory]
        except KeyError:
            return None
    
    def get_status_mapping(self, code):
        """Obtiene el significado de un código de estado."""
        return self.value_mappings['status'].get(str(code), 'Unknown')
    
    def get_error_mapping(self, code):
        """Obtiene el significado de un código de error."""
        return self.value_mappings['errors'].get(str(code), 'Unknown Error')

    def get_supported_oids(self):
        """Obtiene lista de OIDs soportados (no nulos)."""
        supported = {}
        for category, items in self.oids.items():
            supported[category] = {k: v for k, v in items.items() if v is not None}
        return supported