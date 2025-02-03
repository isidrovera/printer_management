# server/app/db/models/printer.py
from app.db.base import BaseModel
from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Float
from sqlalchemy.orm import relationship
from datetime import datetime

class Printer(BaseModel):
    __tablename__ = 'printers'
    
    # Relaciones con Client y Agent
    client_id = Column(Integer, ForeignKey('clients.id'))
    agent_id = Column(Integer, ForeignKey('agents.id'))
    oid_config_id = Column(Integer, ForeignKey('printer_oids.id'))
    
    # Información básica
    name = Column(String, nullable=False)
    model = Column(String)
    brand = Column(String)
    serial_number = Column(String, unique=True)
    ip_address = Column(String, unique=True, nullable=False)
    location = Column(String)
    status = Column(String, default='offline')
    
    # Configuración SNMP
    snmp_version = Column(String, default='2c')
    snmp_community = Column(String, default='public')
    snmp_port = Column(Integer, default=161)
    snmp_timeout = Column(Integer, default=2)
    snmp_retries = Column(Integer, default=3)
    
    # Últimos valores leídos vía SNMP
    last_values = Column(JSON, default={
        'system': {},
        'status': {},
        'supplies': {},
        'counters': {},
        'paper': {}
    })
    
    # Contadores actuales
    counters = Column(JSON, default={
        'total': 0,
        'color': 0,
        'black': 0,
        'duplex': 0,
        'scan': 0,
        'copy': 0,
        'fax': 0
    })
    
    # Estado de consumibles
    supplies = Column(JSON, default={
        'black': {'level': 100, 'max': None, 'type': None},
        'cyan': {'level': 100, 'max': None, 'type': None},
        'magenta': {'level': 100, 'max': None, 'type': None},
        'yellow': {'level': 100, 'max': None, 'type': None},
        'waste': {'level': 0, 'max': None},
        'drum': {'level': 100, 'max': None},
        'fuser': {'level': 100, 'max': None},
        'maintenance_kit': {'level': 100, 'max': None}
    })
    
    # Estado de las bandejas
    paper_trays = Column(JSON, default={
        'tray1': {'status': 'unknown', 'size': None, 'level': None},
        'tray2': {'status': 'unknown', 'size': None, 'level': None},
        'tray3': {'status': 'unknown', 'size': None, 'level': None}
    })
    
    # Configuración y alertas
    settings = Column(JSON, default={
        'alert_levels': {
            'toner': 15,
            'drum': 20,
            'maintenance_kit': 20,
            'paper': 10
        },
        'polling_interval': 300,  # segundos
        'retry_attempts': 3,
        'notifications': {
            'email': True,
            'webhook': False,
            'dashboard': True
        }
    })
    
    # Historial de eventos
    history = Column(JSON, default={
        'errors': [],
        'warnings': [],
        'maintenance': [],
        'supply_changes': [],
        'status_changes': []
    })
    
    # Estado y monitoreo
    is_active = Column(Boolean, default=True)
    last_check = Column(String)
    next_check = Column(String)
    error_count = Column(Integer, default=0)
    consecutive_failures = Column(Integer, default=0)
    
    # Relaciones
    client = relationship("Client", back_populates="printers")
    agent = relationship("Agent", back_populates="printers")
    oid_config = relationship("PrinterOIDs", back_populates="printers")
    printer_jobs = relationship("PrinterJob", back_populates="printer")

    def update_history(self, event_type, event_data):
        """Actualiza el historial con nuevo evento."""
        if event_type in self.history:
            self.history[event_type].append({
                'timestamp': datetime.utcnow().isoformat(),
                'data': event_data
            })
            # Mantener solo últimos 100 eventos por tipo
            if len(self.history[event_type]) > 100:
                self.history[event_type] = self.history[event_type][-100:]

    def update_counter(self, counter_type, value):
        """Actualiza un contador específico."""
        if counter_type in self.counters:
            old_value = self.counters[counter_type]
            self.counters[counter_type] = value
            if value < old_value:
                self.update_history('counters', {
                    'type': counter_type,
                    'reset': True,
                    'old_value': old_value,
                    'new_value': value
                })

    def update_supply(self, supply_type, value, max_value=None, supply_identifier=None):
        """Actualiza nivel de consumible."""
        if supply_type in self.supplies:
            old_value = self.supplies[supply_type]['level']
            self.supplies[supply_type]['level'] = value
            if max_value:
                self.supplies[supply_type]['max'] = max_value
            if supply_identifier:
                self.supplies[supply_type]['type'] = supply_identifier
            
            # Registrar cambio significativo
            if abs(old_value - value) > 5:
                self.update_history('supply_changes', {
                    'type': supply_type,
                    'old_value': old_value,
                    'new_value': value,
                    'max': max_value,
                    'identifier': supply_identifier
                })

    def check_alerts(self):
        """Verifica si hay alertas basadas en niveles configurados."""
        alerts = []
        for supply, data in self.supplies.items():
            if data['level'] <= self.settings['alert_levels'].get(supply, 15):
                alerts.append({
                    'type': 'supply',
                    'item': supply,
                    'level': data['level'],
                    'threshold': self.settings['alert_levels'].get(supply, 15)
                })
        return alerts

    def to_dict(self):
        """Convierte el objeto a diccionario."""
        return {
            "id": self.id,
            "name": self.name,
            "model": self.model,
            "brand": self.brand,
            "serial_number": self.serial_number,
            "ip_address": self.ip_address,
            "location": self.location,
            "status": self.status,
            "is_active": self.is_active,
            "last_check": self.last_check,
            "counters": self.counters,
            "supplies": self.supplies,
            "paper_trays": self.paper_trays,
            "settings": self.settings,
            "agent": self.agent.to_dict() if self.agent else None,
            "client": self.client.to_dict() if self.client else None,
            "alerts": self.check_alerts()
        }