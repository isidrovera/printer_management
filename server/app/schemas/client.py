# server/app/schemas/client.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ClientType(str, Enum):
    CORPORATE = "empresa"       # Valor en DB: "empresa"
    INDIVIDUAL = "individual"
    GOVERNMENT = "government"

class ClientStatus(str, Enum):
    ACTIVE = "activo"           # Valor en DB: "activo"
    INACTIVE = "inactivo"
    PENDING = "pending"

class ClientBase(BaseModel):
    name: str
    business_name: Optional[str] = None
    tax_id: str
    client_code: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    client_type: ClientType
    status: ClientStatus
    service_level: Optional[str] = None
    account_manager: Optional[str] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    is_active: bool = True

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    business_name: Optional[str] = None
    tax_id: Optional[str] = None
    client_code: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    client_type: Optional[ClientType] = None
    status: Optional[ClientStatus] = None
    service_level: Optional[str] = None
    account_manager: Optional[str] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class ClientResponse(ClientBase):
    id: int
    token: str
    created_at: datetime
    updated_at: datetime
    last_contact_date: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class ClientSearch(BaseModel):
    search_term: str

class ClientDashboardStats(BaseModel):
    total: int
    active: int
    inactive: int
    by_type: Dict[str, int]
    active_contracts: int
    last_updated: str
