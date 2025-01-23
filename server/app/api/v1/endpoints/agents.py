# server/app/api/v1/endpoints/agents.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.agent_service import AgentService
from app.schemas.agent import AgentCreate, Agent

router = APIRouter()

@router.post("/register", response_model=Agent)
async def register_agent(
    data: AgentCreate,
    db: Session = Depends(get_db)
):
    agent_service = AgentService(db)
    try:
        agent = await agent_service.register_agent(
            data.client_token,
            data.hostname,
            data.username,
            data.ip_address,
            data.device_type,
            data.system_info
        )
        return agent
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
