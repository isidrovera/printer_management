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
        from_attributes = True