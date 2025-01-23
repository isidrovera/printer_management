# server/app/db/models/agent.py
from app.db.base import BaseModel
from sqlalchemy import Column, String, Boolean, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
import uuid

class Agent(BaseModel):
    __tablename__ = 'agents'
    
    client_id = Column(Integer, ForeignKey('clients.id'))
    token = Column(String, unique=True, nullable=False)
    hostname = Column(String, nullable=False)
    username = Column(String)
    ip_address = Column(String)
    device_type = Column(String)
    system_info = Column(JSON)
    status = Column(String, default='offline')
    is_active = Column(Boolean, default=True)
    
    client = relationship("Client", back_populates="agents")
    printer_jobs = relationship("PrinterJob", back_populates="agent")
    
    @staticmethod
    def generate_token():
        return f"agt_{uuid.uuid4().hex}"
