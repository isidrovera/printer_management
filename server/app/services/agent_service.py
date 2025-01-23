from fastapi import HTTPException
from ..db.models import Agent, Client
from datetime import datetime

class AgentService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def register_agent(
        self, 
        client_token: str,
        hostname: str,
        username: str,
        ip_address: str,
        device_type: str,
        system_info: dict
    ):
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
            status='online'
        )
        
        self.db.add(agent)
        self.db.commit()
        return agent

    async def validate_agent(self, agent_token: str):
        return self.db.query(Agent).filter(
            Agent.token == agent_token,
            Agent.is_active == True
        ).first()

    async def update_status(self, agent_token: str, status: str):
        agent = await self.validate_agent(agent_token)
        if agent:
            agent.status = status
            agent.updated_at = datetime.utcnow()
            self.db.commit()
            return agent
        return None