# server/app/schemas/client.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ClientType(str, Enum):
    CORPORATE = "corporate"
    INDIVIDUAL = "individual"
    GOVERNMENT = "government"

class ClientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

class ClientBase(BaseModel):
    name: str
    business_name: Optional[str]
    tax_id: str
    client_code: str
    contact_email: EmailStr
    phone: Optional[str]
    address: Optional[str]
    client_type: ClientType
    status: ClientStatus
    service_level: Optional[str]
    account_manager: Optional[str]
    contract_start_date: Optional[datetime]
    contract_end_date: Optional[datetime]
    is_active: bool = True

class ClientCreate(ClientBase):
    pass

class ClientUpdate(ClientBase):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    client_code: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    client_type: Optional[ClientType] = None
    status: Optional[ClientStatus] = None

class ClientResponse(ClientBase):
    id: int
    token: str
    created_at: datetime
    updated_at: datetime
    last_contact_date: Optional[datetime]

    class Config:
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