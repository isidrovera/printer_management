# server/app/api/v1/endpoints/agents.py
from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.agent_service import AgentService
from app.schemas.agent import AgentCreate, Agent, AgentUpdate

router = APIRouter()
templates = Jinja2Templates(directory="templates")  # Ajusta si usas otra ruta

@router.get("/", response_class=HTMLResponse)
async def list_agents(request: Request, db: Session = Depends(get_db)):
    """
    Renderiza la lista de agentes con los datos necesarios para la plantilla.
    """
    agent_service = AgentService(db)
    agents = await agent_service.get_agents(skip=0, limit=100)  # Obtiene los agentes
    drivers = await agent_service.get_drivers()  # Obtiene la lista de drivers (ajusta el método)
    return templates.TemplateResponse(
        "agents/agents.html",  # Usa el archivo correcto dentro de tu estructura de templates
        {"request": request, "agents": agents, "drivers": drivers},
    )

@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(data: AgentCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo agente en la base de datos.
    """
    agent_service = AgentService(db)
    try:
        return await agent_service.create_agent(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """
    Elimina un agente dado su ID.
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

    # Buscar el agente en la base de datos por su token
    existing_agent = await agent_service.get_agent_by_token(data.agent_token)
    if not existing_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Actualizar la información del agente
    updated_agent = await agent_service.update_agent(existing_agent.id, data.dict(exclude_unset=True))
    
    if not updated_agent:
        raise HTTPException(status_code=400, detail="Error updating agent")
    
    return updated_agent
@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """
    Obtiene la información detallada de un agente por su ID.
    """
    agent_service = AgentService(db)
    agent = await agent_service.get_agent(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent

@router.post("/register", response_model=Agent)
async def register_agent(data: AgentCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo agente en la base de datos.
    """
    agent_service = AgentService(db)
    
    try:
        agent = await agent_service.register_agent(
            client_token=data.client_token,
            hostname=data.hostname,
            username=data.username,
            ip_address=data.ip_address,
            device_type=data.device_type,
            system_info=data.system_info
        )
        return agent
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
