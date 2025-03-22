# server/app/schemas/agent.py
from pydantic import BaseModel
from typing import Dict, Optional

class AgentBase(BaseModel):
    hostname: str
    username: str
    ip_address: str
    device_type: str
    system_info: Dict

class AgentCreate(AgentBase):
    client_token: str

class Agent(AgentBase):
    id: int
    token: str
    status: str

    class Config:
        orm_mode = True  # Permite que Pydantic trabaje con modelos ORM

class AgentUpdate(BaseModel):
    agent_token: str  # Se utiliza para identificar el agente
    hostname: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    system_info: Optional[Dict] = None
