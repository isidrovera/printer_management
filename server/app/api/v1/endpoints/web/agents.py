from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional, List
from datetime import datetime
from app.db.session import get_db
from app.services.agent_service import AgentService
from app.services.driver_service import DriverService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Lista de agentes
@router.get("/agents")
async def list_agents(request: Request, db: Session = Depends(get_db)):
    try:
        agent_service = AgentService(db)
        agents = await agent_service.get_agents(skip=0, limit=100)
        print(f"Agentes obtenidos: {agents}")  # Debug
        drivers = await agent_service.get_drivers()
        print(f"Drivers obtenidos: {drivers}")  # Debug
        return templates.TemplateResponse(
            "agents/agents.html",
            {"request": request, "agents": agents, "drivers": drivers}
        )
    except Exception as e:
        logger.error(f"Error listando agentes: {str(e)}")
        return templates.TemplateResponse(
            "agents/agents.html",
            {"request": request, "agents": [], "drivers": [], "error": str(e)}
        )

# Crear agente
@router.get("/agents/create")
async def create_agent_form(request: Request, db: Session = Depends(get_db)):
    try:
        driver_service = DriverService(db)
        drivers = await driver_service.get_all()
        return templates.TemplateResponse(
            "agents/form.html",
            {
                "request": request,
                "agent": None,
                "drivers": drivers
            }
        )
    except Exception as e:
        logger.error(f"Error en formulario de creación de agente: {str(e)}")
        return templates.TemplateResponse(
            "agents/form.html",
            {
                "request": request,
                "agent": None,
                "drivers": [],
                "error": str(e)
            }
        )

@router.post("/agents/create")
async def create_agent(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        agent_service = AgentService(db)
        
        agent_data = {
            "name": form.get("name"),
            "description": form.get("description"),
            "status": "offline",  # Estado inicial
            "last_seen": datetime.utcnow(),
            "configuration": {
                "polling_interval": int(form.get("polling_interval", 300)),
                "log_level": form.get("log_level", "INFO"),
                "enabled_services": form.getlist("enabled_services", [])
            }
        }
        
        agent = await agent_service.create(agent_data)
        logger.info(f"Agente creado exitosamente: {agent.name}")
        return RedirectResponse("/agents", status_code=303)
        
    except Exception as e:
        logger.error(f"Error creando agente: {str(e)}")
        return templates.TemplateResponse(
            "agents/form.html",
            {
                "request": request,
                "agent": None,
                "error": str(e),
                "form_data": form
            }
        )

# Editar agente
@router.get("/agents/{agent_id}/edit")
async def edit_agent_form(request: Request, agent_id: int, db: Session = Depends(get_db)):
    try:
        agent_service = AgentService(db)
        agent = await agent_service.get_by_id(agent_id)
        
        if not agent:
            return RedirectResponse("/agents", status_code=303)
            
        driver_service = DriverService(db)
        drivers = await driver_service.get_all()
        
        return templates.TemplateResponse(
            "agents/form.html",
            {
                "request": request,
                "agent": agent,
                "drivers": drivers
            }
        )
    except Exception as e:
        logger.error(f"Error en formulario de edición de agente: {str(e)}")
        return templates.TemplateResponse(
            "agents/form.html",
            {
                "request": request,
                "agent": None,
                "drivers": [],
                "error": str(e)
            }
        )

@router.post("/agents/{agent_id}/edit")
async def edit_agent(request: Request, agent_id: int, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        agent_service = AgentService(db)
        
        agent_data = {
            "name": form.get("name"),
            "description": form.get("description"),
            "configuration": {
                "polling_interval": int(form.get("polling_interval", 300)),
                "log_level": form.get("log_level", "INFO"),
                "enabled_services": form.getlist("enabled_services", [])
            },
            "updated_at": datetime.utcnow()
        }
        
        agent = await agent_service.update(agent_id, agent_data)
        
        if not agent:
            raise ValueError("Agente no encontrado")
            
        logger.info(f"Agente {agent_id} actualizado exitosamente")
        return RedirectResponse("/agents", status_code=303)
        
    except ValueError as e:
        logger.error(f"Error de validación al actualizar agente: {str(e)}")
        return templates.TemplateResponse(
            "agents/form.html",
            {
                "request": request,
                "agent": {"id": agent_id, **form},
                "error": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error al actualizar agente: {str(e)}")
        return templates.TemplateResponse(
            "agents/form.html",
            {
                "request": request,
                "agent": {"id": agent_id, **form},
                "error": "Error al actualizar el agente. Por favor, intente nuevamente."
            }
        )

# Eliminar agente
@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    try:
        agent_service = AgentService(db)
        deleted = await agent_service.delete(agent_id)
        
        if deleted:
            return {"success": True}
            
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Agente no encontrado"}
        )
    except Exception as e:
        logger.error(f"Error eliminando agente: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Ver detalles del agente
@router.get("/agents/{agent_id}/details")
async def agent_details(request: Request, agent_id: int, db: Session = Depends(get_db)):
    try:
        agent_service = AgentService(db)
        agent = await agent_service.get_by_id(agent_id)
        
        if not agent:
            return RedirectResponse("/agents", status_code=303)
            
        return templates.TemplateResponse(
            "agents/details.html",
            {"request": request, "agent": agent}
        )
    except Exception as e:
        logger.error(f"Error obteniendo detalles del agente: {str(e)}")
        return templates.TemplateResponse(
            "agents/details.html",
            {
                "request": request,
                "agent": None,
                "error": str(e)
            }
        )

# Actualizar estado del agente
@router.post("/agents/{agent_id}/status")
async def update_agent_status(agent_id: int, status: str, db: Session = Depends(get_db)):
    try:
        agent_service = AgentService(db)
        updated = await agent_service.update_status(agent_id, status)
        
        if not updated:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Agente no encontrado"}
            )
            
        return {"success": True}
    except Exception as e:
        logger.error(f"Error actualizando estado del agente: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Asignar drivers al agente
@router.post("/agents/{agent_id}/drivers")
async def assign_drivers(
    agent_id: int,
    driver_ids: List[int],
    db: Session = Depends(get_db)
):
    try:
        agent_service = AgentService(db)
        await agent_service.assign_drivers(agent_id, driver_ids)
        return {"success": True}
    except Exception as e:
        logger.error(f"Error asignando drivers al agente: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Obtener configuración del agente
@router.get("/agents/{agent_id}/config")
async def get_agent_config(agent_id: int, db: Session = Depends(get_db)):
    try:
        agent_service = AgentService(db)
        config = await agent_service.get_config(agent_id)
        
        if not config:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
            
        return config
    except Exception as e:
        logger.error(f"Error obteniendo configuración del agente: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Actualizar configuración del agente
@router.post("/agents/{agent_id}/config")
async def update_agent_config(
    agent_id: int,
    config: dict,
    db: Session = Depends(get_db)
):
    try:
        agent_service = AgentService(db)
        updated = await agent_service.update_config(agent_id, config)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Agente no encontrado")
            
        return {"success": True}
    except Exception as e:
        logger.error(f"Error actualizando configuración del agente: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))