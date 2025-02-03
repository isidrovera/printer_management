# server/app/schemas/printer_oids.py
from pydantic import BaseModel
from typing import Dict, Optional

class PrinterBase(BaseModel):
    name: str
    brand: str
    model: str
    ip_address: str
    client_id: int
    agent_id: Optional[int] = None
    location: Optional[str] = None
    oid_config_id: int

class PrinterCreate(PrinterBase):
    serial_number: Optional[str] = None
    snmp_version: Optional[str] = "2c"
    snmp_community: Optional[str] = "public"
    snmp_port: Optional[int] = 161

class Printer(PrinterBase):
    id: int
    status: str
    serial_number: Optional[str]
    counters: Dict
    supplies: Dict
    last_check: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

class PrinterUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    snmp_version: Optional[str] = None
    snmp_community: Optional[str] = None
    snmp_port: Optional[int] = None
    settings: Optional[Dict] = None
    is_active: Optional[bool] = None


class PrinterOIDsCreate(PrinterBase):
    serial_number: Optional[str] = None
    snmp_version: Optional[str] = "2c"
    snmp_community: Optional[str] = "public"
    snmp_port: Optional[int] = 161
