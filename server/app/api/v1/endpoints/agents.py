# server/app/api/v1/endpoints/agents.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.agent_service import AgentService
from app.schemas.agent import AgentCreate, Agent, AgentUpdate

router = APIRouter()

@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(data: AgentCreate, db: Session = Depends(get_db)):
    agent_service = AgentService(db)
    try:
        return await agent_service.create_agent(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[Agent])
async def list_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    agent_service = AgentService(db)
    return await agent_service.get_agents(skip, limit)

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent_service = AgentService(db)
    agent = await agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(agent_id: int, data: AgentUpdate, db: Session = Depends(get_db)):
    agent_service = AgentService(db)
    agent = await agent_service.update_agent(agent_id, data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    agent_service = AgentService(db)
    if not await agent_service.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
