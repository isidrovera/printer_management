# server/app/db/models/printer.py
from server.app.db.base import BaseModel
from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class Printer(BaseModel):
    __tablename__ = 'printers'
    
    # Relaciones básicas
    client_id = Column(Integer, ForeignKey('clients.id'))
    agent_id = Column(Integer, ForeignKey('agents.id'))
    oid_config_id = Column(Integer, ForeignKey('printer_oids.id'), nullable=False)
    oid_config = relationship("PrinterOIDs", back_populates="printers")
    
    # Información básica de identificación
    name = Column(String, nullable=False)
    model = Column(String)
    brand = Column(String)
    serial_number = Column(String, unique=True)
    ip_address = Column(String, unique=True, nullable=False)
    location = Column(String)
    printer_jobs = relationship("PrinterJob", back_populates="printer")
    # Estado actual de la impresora
    status = Column(String, default='offline')
    is_active = Column(Boolean, default=True)
    last_check = Column(DateTime, nullable=True)
    
    # Datos detallados reportados por el agente
    printer_data = Column(JSON, default={
        # Contadores detallados de impresión
        'counters': {
            'total': 0,
            'color': {
                'total': 0,
                'cyan': 0,
                'magenta': 0,
                'yellow': 0,
                'black': 0
            },
            'black_white': 0,
            'duplex': 0,
            'simplex': 0,
            'a4': 0,
            'a3': 0,
            'letter': 0,
            'legal': 0
        },
        
        # Estado de consumibles
        'supplies': {
            'toners': {
                'black': {
                    'current_level': 0,
                    'max_level': 0,
                    'percentage': 0,
                    'status': 'ok'
                },
                'cyan': {
                    'current_level': 0,
                    'max_level': 0,
                    'percentage': 0,
                    'status': 'ok'
                },
                'magenta': {
                    'current_level': 0,
                    'max_level': 0,
                    'percentage': 0,
                    'status': 'ok'
                },
                'yellow': {
                    'current_level': 0,
                    'max_level': 0,
                    'percentage': 0,
                    'status': 'ok'
                }
            },
            'drums': {
                'black': {
                    'current_level': 0,
                    'max_level': 0,
                    'percentage': 0,
                    'status': 'ok'
                },
                'color': {
                    'current_level': 0,
                    'max_level': 0,
                    'percentage': 0,
                    'status': 'ok'
                }
            },
            'maintenance_kit': {
                'current_level': 0,
                'max_level': 0,
                'percentage': 0,
                'status': 'ok'
            },
            'waste_toner_box': {
                'current_level': 0,
                'max_level': 0,
                'percentage': 0,
                'status': 'ok'
            }
        },
        
        # Estado de bandejas de papel
        'paper_trays': {
            'tray1': {
                'size': None,
                'type': None,
                'current_level': 0,
                'max_level': 0,
                'percentage': 0,
                'status': 'unknown'
            },
            'tray2': {
                'size': None,
                'type': None,
                'current_level': 0,
                'max_level': 0,
                'percentage': 0,
                'status': 'unknown'
            },
            'tray3': {
                'size': None,
                'type': None,
                'current_level': 0,
                'max_level': 0,
                'percentage': 0,
                'status': 'unknown'
            }
        },
        
        # Información del sistema
        'system': {
            'temperature': 0,
            'power_on_time': 0,
            'firmware_version': None,
            'serial_number': None
        },
        
        # Alertas y errores
        'alerts': [],
        'errors': []
    })
    
    # Historial de datos (últimos 100 registros)
    data_history = Column(JSON, default={
        'counters': [],
        'supplies': [],
        'errors': [],
        'status_changes': []
    })
    
    # Relaciones
    client = relationship("Client", back_populates="printers")
    agent = relationship("Agent", back_populates="printers")
    printer_jobs = relationship("PrinterJob", back_populates="printer")
    
    def update_printer_data(self, data):
        """
        Actualiza todos los datos de la impresora de una sola vez.
        
        :param data: Diccionario completo con los datos de la impresora
        """
        # Actualizar datos actuales
        self.printer_data = data
        
        # Registrar en histórico
        for key in ['counters', 'supplies', 'errors']:
            if key in data:
                log_entry = {
                    'timestamp': datetime.utcnow(),
                    'data': data[key]
                }
                
                # Añadir nueva entrada y mantener solo los últimos 100 registros
                self.data_history[key].append(log_entry)
                if len(self.data_history[key]) > 100:
                    self.data_history[key] = self.data_history[key][-100:]
        
        # Actualizar última verificación y estado
        self.last_check = datetime.utcnow()
        if 'status' in data:
            self.status = data['status']
    
    def check_critical_supplies(self):
        """
        Verifica el estado crítico de los consumibles.
        
        :return: Lista de consumibles en estado crítico
        """
        critical_supplies = []
        
        # Verificar toners
        for color, toner in self.printer_data['supplies']['toners'].items():
            if toner['percentage'] < 10:
                critical_supplies.append({
                    'type': f'{color} toner',
                    'current_level': toner['current_level'],
                    'percentage': toner['percentage']
                })
        
        # Verificar otros consumibles
        for supply_type in ['drums', 'maintenance_kit', 'waste_toner_box']:
            supply = self.printer_data['supplies'].get(supply_type)
            if supply and supply['percentage'] < 15:
                critical_supplies.append({
                    'type': supply_type,
                    'current_level': supply['current_level'],
                    'percentage': supply['percentage']
                })
        
        return critical_supplies
    
    def to_dict(self):
        """Convierte el objeto a diccionario para serialización."""
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
            "printer_data": self.printer_data,
            "critical_supplies": self.check_critical_supplies(),
            "client": self.client.to_dict() if self.client else None,
            "agent": self.agent.to_dict() if self.agent else None
        }