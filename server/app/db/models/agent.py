# server/app/db/models/agent.py
from app.db.base import BaseModel
from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer, Float, DateTime, TIMESTAMP
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class Agent(BaseModel):
    __tablename__ = 'agents'
    
    client_id = Column(Integer, ForeignKey('clients.id'))
    token = Column(String, unique=True, nullable=False)
    hostname = Column(String, nullable=False)
    username = Column(String)
    ip_address = Column(String)
    device_type = Column(String)
    system_info = Column(JSON)  # Información completa del sistema
    cpu_info = Column(JSON)  # Información del procesador
    memory_info = Column(JSON)  # Información de la memoria RAM
    disk_info = Column(JSON)  # Información de los discos
    network_info = Column(JSON)  # Información de la red
    gpu_info = Column(JSON)  # Información de la GPU
    battery_info = Column(JSON)  # Información de la batería
    disk_usage = Column(JSON)  # Espacio en disco usado/libre
    status = Column(String, default='offline')
    is_active = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)  # Nuevo campo para heartbeat
    last_startup = Column(TIMESTAMP(timezone=True))
    last_shutdown = Column(TIMESTAMP(timezone=True))
    last_reconnection = Column(TIMESTAMP(timezone=True))
   
    client = relationship("Client", back_populates="agents")
    printer_jobs = relationship("PrinterJob", back_populates="agent")
    printers = relationship("Printer", back_populates="agent")
    tunnels = relationship("Tunnel", back_populates="agent", cascade="all, delete-orphan")
    
    @staticmethod
    def generate_token():
        return f"agt_{uuid.uuid4().hex}"