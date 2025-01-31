# server/app/schemas/tunnel.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TunnelCreate(BaseModel):
    agent_id: int
    ssh_host: str
    ssh_port: int = 22
    username: str
    password: str
    local_port: int
    remote_host: str
    remote_port: int
    description: Optional[str] = None

class TunnelResponse(BaseModel):
    id: int 
    tunnel_id: str
    remote_host: str
    remote_port: int
    local_port: int
    status: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True