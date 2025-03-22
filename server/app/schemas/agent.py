# server/app/schemas/agent.py
from pydantic import BaseModel
from typing import Dict, Optional, List

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
        orm_mode = True  # Habilita la conversión desde instancias ORM

class AgentUpdate(BaseModel):
    agent_token: str  # Se utiliza para identificar el agente
    hostname: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    system_info: Optional[Dict] = None

class AgentsResponse(BaseModel):
    agents: List[Agent]
    drivers: List[Dict]  # Si tienes un esquema para drivers, reemplaza Dict por ese esquema

    class Config:
        orm_mode = True
