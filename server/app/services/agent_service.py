from fastapi import HTTPException
from ..db.models import Agent, Client
from datetime import datetime
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

class AgentService:
   def __init__(self, db_session: Session):
       self.db = db_session

   async def register_agent(
       self, 
       client_token: str,
       hostname: str,
       username: str,
       ip_address: str,
       device_type: str,
       system_info: dict
   ) -> Agent:
       client = self.db.query(Client).filter(Client.token == client_token).first()
       if not client:
           raise HTTPException(status_code=401, detail="Invalid client token")
       
       agent = Agent(
           client_id=client.id,
           token=Agent.generate_token(),
           hostname=hostname,
           username=username,
           ip_address=ip_address,
           device_type=device_type,
           system_info=system_info,
           status='online',
           is_active=True,
           created_at=datetime.utcnow(),
           updated_at=datetime.utcnow()
       )
       
       self.db.add(agent)
       self.db.commit()
       self.db.refresh(agent)
       return agent

   async def validate_agent(self, agent_token: str) -> Optional[Agent]:
       return self.db.query(Agent).filter(
           Agent.token == agent_token,
           Agent.is_active == True
       ).first()

   async def update_status(self, agent_token: str, status: str) -> Optional[Agent]:
       agent = await self.validate_agent(agent_token)
       if agent:
           agent.status = status
           agent.updated_at = datetime.utcnow()
           self.db.commit()
           self.db.refresh(agent)
           return agent
       return None

   async def get_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
       return self.db.query(Agent)\
                    .filter(Agent.is_active == True)\
                    .offset(skip)\
                    .limit(limit)\
                    .all()

   async def get_agent(self, agent_id: int) -> Optional[Agent]:
       return self.db.query(Agent)\
                    .filter(Agent.id == agent_id, Agent.is_active == True)\
                    .first()

   async def create_agent(self, data: Dict) -> Agent:
       agent = Agent(**data)
       self.db.add(agent)
       self.db.commit()
       self.db.refresh(agent)
       return agent

   async def update_agent(self, agent_id: int, data: Dict) -> Optional[Agent]:
       agent = await self.get_agent(agent_id)
       if not agent:
           return None
       
       for key, value in data.items():
           if hasattr(agent, key):
               setattr(agent, key, value)
       
       agent.updated_at = datetime.utcnow()
       self.db.commit()
       self.db.refresh(agent)
       return agent

   async def delete_agent(self, agent_id: int) -> bool:
       agent = await self.get_agent(agent_id)
       if not agent:
           return False
       
       agent.is_active = False
       agent.updated_at = datetime.utcnow()
       self.db.commit()
       return True

   async def get_drivers(self) -> List[Dict]:
       """
       Obtiene la lista de drivers disponibles
       Implementar según necesidades
       """
       return []

   async def get_agent_by_token(self, token: str) -> Optional[Agent]:
       return self.db.query(Agent)\
                    .filter(Agent.token == token, Agent.is_active == True)\
                    .first()