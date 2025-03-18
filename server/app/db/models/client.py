# server/app/db/models/client.py

from app.db.base import BaseModel
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum, Integer, TIMESTAMP
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

class ClientType(str, enum.Enum):
    EMPRESA = "empresa"
    PERSONAL = "personal"
    GOBIERNO = "gobierno"
    EDUCACION = "educacion"

class ClientStatus(str, enum.Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    SUSPENDIDO = "suspendido"
    PENDIENTE = "pendiente"

class Client(BaseModel):
    __tablename__ = 'clients'
    
    # Información básica
    name = Column(String(100), nullable=False)
    business_name = Column(String(150))
    tax_id = Column(String(20))
    client_type = Column(Enum(ClientType), default=ClientType.EMPRESA)
    client_code = Column(String(20), unique=True)
    
    # Contacto principal
    contact_name = Column(String(100))
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    
    # Contacto técnico
    technical_contact_name = Column(String(100))
    technical_contact_email = Column(String(100))
    technical_contact_phone = Column(String(20))
    
    # Contacto facturación
    billing_contact_name = Column(String(100))
    billing_contact_email = Column(String(100))
    billing_contact_phone = Column(String(20))
    
    # Dirección fiscal
    billing_address = Column(String(200))
    billing_city = Column(String(100))
    billing_state = Column(String(100))
    billing_zip_code = Column(String(10))
    billing_country = Column(String(100))
    
    # Dirección de servicio
    service_address = Column(String(200))
    service_city = Column(String(100))
    service_state = Column(String(100))
    service_zip_code = Column(String(10))
    service_country = Column(String(100))
    
    # Información comercial
    contract_number = Column(String(50))
    contract_start_date = Column(TIMESTAMP)
    contract_end_date = Column(TIMESTAMP)
    payment_terms = Column(String(100))
    credit_limit = Column(Integer)
    
    # Información de gestión
    account_manager = Column(String(100))
    service_level = Column(String(50))
    support_priority = Column(Integer)
    
    # Estado y configuración
    status = Column(Enum(ClientStatus), default=ClientStatus.ACTIVO)
    is_active = Column(Boolean, default=True)
    token = Column(String, unique=True, nullable=False)
    notes = Column(Text)
    
    # Fechas importantes
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contact_date = Column(TIMESTAMP)
    
    # Relaciones
    agents = relationship("Agent", back_populates="client")
    printers = relationship("Printer", back_populates="client")

    @staticmethod
    def generate_token():
        return f"cli_{uuid.uuid4().hex}"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.token:
            self.token = self.generate_token()
        if not self.client_code:
            self.client_code = f"C{uuid.uuid4().hex[:8].upper()}"
    
    def to_dict(self):
        """Convierte el objeto a diccionario para serialización"""
        return {
            "id": self.id,
            "name": self.name,
            "business_name": self.business_name,
            "tax_id": self.tax_id,
            "client_type": self.client_type.value if self.client_type else None,
            "client_code": self.client_code,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "status": self.status.value if self.status else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "contract_number": self.contract_number,
            "service_level": self.service_level
        }