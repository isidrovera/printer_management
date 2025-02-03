# server/app/db/models/client.py
from app.db.base import BaseModel
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
import uuid

class Client(BaseModel):
    __tablename__ = 'clients'
    
    name = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    
    agents = relationship("Agent", back_populates="client")
    printers = relationship("Printer", back_populates="client")
    
    @staticmethod
    def generate_token():
        return f"cli_{uuid.uuid4().hex}"
