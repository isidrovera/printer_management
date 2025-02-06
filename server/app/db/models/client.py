# server/app/db/models/client.py
from app.db.base import BaseModel
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum, Integer
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

# Definir las enumeraciones
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
    # ... resto del código del modelo ...
    
    # Información básica
    name = Column(String(100), nullable=False)
    business_name = Column(String(150))  # Razón social
    tax_id = Column(String(20))  # RFC o identificación fiscal
    client_type = Column(Enum(ClientType), default=ClientType.EMPRESA)
    client_code = Column(String(20), unique=True)  # Código interno del cliente
    
    # Contacto principal
    contact_name = Column(String(100))
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    contact_position = Column(String(50))
    
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
    billing_country = Column(String(100), default="México")
    
    # Dirección de servicio (si es diferente a la fiscal)
    service_address = Column(String(200))
    service_city = Column(String(100))
    service_state = Column(String(100))
    service_zip_code = Column(String(10))
    service_country = Column(String(100), default="México")
    
    # Información comercial
    contract_number = Column(String(50))
    contract_start_date = Column(DateTime)
    contract_end_date = Column(DateTime)
    payment_terms = Column(String(100))  # Términos de pago (30 días, 60 días, etc.)
    credit_limit = Column(Integer)  # Límite de crédito
    
    # Información de gestión
    account_manager = Column(String(100))  # Ejecutivo de cuenta asignado
    service_level = Column(String(50))  # Nivel de servicio contratado
    support_priority = Column(Integer)  # Prioridad de soporte (1-5)
    
    # Estado y configuración
    status = Column(Enum(ClientStatus), default=ClientStatus.ACTIVO)
    is_active = Column(Boolean, default=True)
    token = Column(String, unique=True, nullable=False)
    notes = Column(Text)  # Notas generales sobre el cliente
    
    # Fechas importantes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_contact_date = Column(DateTime)  # Última fecha de contacto
    
    # Relaciones
    agents = relationship("Agent", back_populates="client")
    printers = relationship("Printer", back_populates="client")
    
    @staticmethod
    def generate_token():
        return f"cli_{uuid.uuid4().hex}"
    
    @staticmethod
    def generate_client_code():
        """Genera un código único para el cliente"""
        return f"C{uuid.uuid4().hex[:8].upper()}"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.token:
            self.token = self.generate_token()
        if not self.client_code:
            self.client_code = self.generate_client_code()
    
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