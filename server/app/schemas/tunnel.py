# server/app/schemas/tunnel.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TunnelCreate(BaseModel):
    agent_id: int
    remote_host: str
    remote_port: int
    local_port: int
    username: str
    password: str
    description: Optional[str] = None

class TunnelResponse(BaseModel):
    id: int
    agent_id: int
    tunnel_id: str
    remote_host: str
    remote_port: int
    local_port: int
    status: str
    created_at: datetime
    description: Optional[str] = None

    class Config:
        from_attributes = True