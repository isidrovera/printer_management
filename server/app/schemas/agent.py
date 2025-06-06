# server/app/schemas/agent.py
from pydantic import BaseModel, ConfigDict
from typing import Dict, Optional, List

class AgentBase(BaseModel):
    hostname: str
    username: str
    ip_address: str
    device_type: str
    system_info: Dict
    
    # Configuración para Pydantic v2
    model_config = ConfigDict(from_attributes=True)

class AgentCreate(AgentBase):
    client_token: str

class Agent(AgentBase):
    id: int
    token: str
    status: str
    
    # Si necesitas mantener compatibilidad con código que usa .from_orm()
    @classmethod
    def from_orm(cls, obj):
        return cls.model_validate(obj)

class AgentUpdate(BaseModel):
    agent_token: str  # Se utiliza para identificar el agente
    hostname: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    system_info: Optional[Dict] = None
    
    model_config = ConfigDict(from_attributes=True)

class AgentsResponse(BaseModel):
    agents: List[Agent]
    drivers: List[Dict]  # Si tienes un esquema para drivers, reemplaza Dict por ese esquema
    
    model_config = ConfigDict(from_attributes=True)