# server/app/api/v1/endpoints/agents.py
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.agent_service import AgentService
from app.schemas.agent import AgentCreate, Agent, AgentUpdate, AgentsResponse

router = APIRouter()

@router.get("/", response_model=AgentsResponse)
async def list_agents(db: Session = Depends(get_db)):
    """
    Devuelve la lista de agentes y drivers en formato JSON.
    Se realiza la conversión explícita de las instancias ORM a modelos Pydantic.
    """
    agent_service = AgentService(db)
    agents = agent_service.get_all()  # Retorna una lista de instancias SQLAlchemy
    drivers = await agent_service.get_drivers()  # Actualmente retorna una lista vacía o la lógica que implementes

    # Convertir cada agente a un modelo Pydantic usando model_validate en lugar de from_orm
    agents_data = [Agent.model_validate(agent) for agent in agents]
    return AgentsResponse(agents=agents_data, drivers=drivers)

@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(data: AgentCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo agente en la base de datos.
    """
    agent_service = AgentService(db)
    try:
        agent = await agent_service.create_agent(data)
        return Agent.model_validate(agent)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """
    Desactiva (elimina lógicamente) un agente dado su ID.
    """
    agent_service = AgentService(db)
    if not await agent_service.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")

@router.put("/update", response_model=Agent)
async def update_agent_info(data: AgentUpdate, db: Session = Depends(get_db)):
    """
    Actualiza la información de un agente existente.
    """
    agent_service = AgentService(db)
    # Buscar el agente en la base de datos mediante su token
    existing_agent = await agent_service.get_agent_by_token(data.agent_token)
    if not existing_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Actualizar la información del agente
    # Nota: en Pydantic v2, dict() está deprecado, usar model_dump()
    updated_agent = await agent_service.update_agent(existing_agent.id, data.model_dump(exclude_unset=True))
    if not updated_agent:
        raise HTTPException(status_code=400, detail="Error updating agent")
    
    return Agent.model_validate(updated_agent)

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """
    Obtiene la información detallada de un agente por su ID.
    """
    agent_service = AgentService(db)
    agent = await agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return Agent.model_validate(agent)

@router.post("/register", response_model=Agent)
async def register_agent(data: AgentCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo agente en el sistema.
    """
    agent_service = AgentService(db)
    agent = await agent_service.register_agent(
        client_token=data.client_token,
        hostname=data.hostname,
        username=data.username,
        ip_address=data.ip_address,
        device_type=data.device_type,
        system_info=data.system_info
    )
    return Agent.model_validate(agent)