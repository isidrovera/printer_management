# server/app/schemas/tunnel.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TunnelCreate(BaseModel):
    agent_id: int
    ssh_host: str      # Servidor SSH al que nos conectaremos
    ssh_port: int = 22 # Puerto SSH del servidor
    username: str      # Usuario SSH
    password: str      # Contraseña SSH
    local_port: int    # Puerto local en Windows
    remote_host: str   # Host al que queremos acceder a través del túnel
    remote_port: int

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