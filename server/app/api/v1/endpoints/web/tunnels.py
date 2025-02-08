from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional, List
from datetime import datetime
from app.db.session import get_db
from app.services.tunnel_service import TunnelService
from app.services.client_service import ClientService
from app.services.agent_service import AgentService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/tunnels")
async def list_tunnels_view(request: Request, db: Session = Depends(get_db)):
    """
    Vista principal de túneles que muestra la lista de todos los túneles activos e inactivos
    """
    try:
        tunnel_service = TunnelService(db)
        tunnels = await tunnel_service.list_tunnels()
        return templates.TemplateResponse(
            "tunnels/list.html",
            {
                "request": request,
                "tunnels": tunnels
            }
        )
    except Exception as e:
        logger.error(f"Error listando túneles: {str(e)}")
        return templates.TemplateResponse(
            "tunnels/list.html",
            {
                "request": request,
                "tunnels": [],
                "error": str(e)
            }
        )

@router.get("/tunnels/create")
async def create_tunnel_form(request: Request, db: Session = Depends(get_db)):
    """
    Formulario para crear un nuevo túnel
    """
    try:
        # Obtener listas de clientes y agentes para el formulario
        client_service = ClientService(db)
        agent_service = AgentService(db)
        
        clients = await client_service.get_all()
        agents = await agent_service.get_all()
        
        return templates.TemplateResponse(
            "tunnels/form.html",
            {
                "request": request,
                "tunnel": None,
                "clients": clients,
                "agents": agents
            }
        )
    except Exception as e:
        logger.error(f"Error cargando formulario de túnel: {str(e)}")
        return templates.TemplateResponse(
            "tunnels/form.html",
            {
                "request": request,
                "tunnel": None,
                "clients": [],
                "agents": [],
                "error": str(e)
            }
        )

@router.post("/tunnels/create")
async def create_tunnel(request: Request, db: Session = Depends(get_db)):
    """
    Procesa la creación de un nuevo túnel
    """
    try:
        form = await request.form()
        tunnel_service = TunnelService(db)
        
        # Validar datos requeridos
        if not all([form.get("name"), form.get("client_id"), form.get("agent_id")]):
            raise ValueError("Todos los campos son requeridos")
            
        tunnel_data = {
            "name": form.get("name"),
            "description": form.get("description"),
            "client_id": int(form.get("client_id")),
            "agent_id": int(form.get("agent_id")),
            "local_port": int(form.get("local_port", 0)),
            "remote_port": int(form.get("remote_port", 0)),
            "remote_host": form.get("remote_host"),
            "tunnel_type": form.get("tunnel_type", "tcp"),
            "status": "inactive",
            "config": {
                "auto_start": form.get("auto_start") == "true",
                "retry_interval": int(form.get("retry_interval", 30)),
                "max_retries": int(form.get("max_retries", 3))
            }
        }
        
        tunnel = await tunnel_service.create_tunnel(tunnel_data)
        logger.info(f"Túnel creado exitosamente: {tunnel.name}")
        
        return RedirectResponse("/tunnels", status_code=303)
        
    except ValueError as e:
        logger.error(f"Error de validación al crear túnel: {str(e)}")
        return templates.TemplateResponse(
            "tunnels/form.html",
            {
                "request": request,
                "tunnel": None,
                "error": str(e),
                "form_data": form
            }
        )
    except Exception as e:
        logger.error(f"Error creando túnel: {str(e)}")
        return templates.TemplateResponse(
            "tunnels/form.html",
            {
                "request": request,
                "tunnel": None,
                "error": "Error interno al crear el túnel"
            }
        )

@router.get("/tunnels/{tunnel_id}/edit")
async def edit_tunnel_form(request: Request, tunnel_id: int, db: Session = Depends(get_db)):
    """
    Formulario para editar un túnel existente
    """
    try:
        tunnel_service = TunnelService(db)
        client_service = ClientService(db)
        agent_service = AgentService(db)
        
        tunnel = await tunnel_service.get_by_id(tunnel_id)
        if not tunnel:
            return RedirectResponse("/tunnels", status_code=303)
            
        clients = await client_service.get_all()
        agents = await agent_service.get_all()
        
        return templates.TemplateResponse(
            "tunnels/form.html",
            {
                "request": request,
                "tunnel": tunnel,
                "clients": clients,
                "agents": agents
            }
        )
    except Exception as e:
        logger.error(f"Error cargando formulario de edición: {str(e)}")
        return RedirectResponse("/tunnels", status_code=303)

@router.post("/tunnels/{tunnel_id}/edit")
async def edit_tunnel(request: Request, tunnel_id: int, db: Session = Depends(get_db)):
    """
    Procesa la actualización de un túnel existente
    """
    try:
        form = await request.form()
        tunnel_service = TunnelService(db)
        
        tunnel_data = {
            "name": form.get("name"),
            "description": form.get("description"),
            "client_id": int(form.get("client_id")),
            "agent_id": int(form.get("agent_id")),
            "local_port": int(form.get("local_port", 0)),
            "remote_port": int(form.get("remote_port", 0)),
            "remote_host": form.get("remote_host"),
            "tunnel_type": form.get("tunnel_type"),
            "config": {
                "auto_start": form.get("auto_start") == "true",
                "retry_interval": int(form.get("retry_interval", 30)),
                "max_retries": int(form.get("max_retries", 3))
            },
            "updated_at": datetime.utcnow()
        }
        
        tunnel = await tunnel_service.update_tunnel(tunnel_id, tunnel_data)
        
        if not tunnel:
            raise ValueError("Túnel no encontrado")
            
        logger.info(f"Túnel {tunnel_id} actualizado exitosamente")
        return RedirectResponse("/tunnels", status_code=303)
        
    except Exception as e:
        logger.error(f"Error actualizando túnel: {str(e)}")
        return templates.TemplateResponse(
            "tunnels/form.html",
            {
                "request": request,
                "tunnel": {"id": tunnel_id, **form},
                "error": str(e)
            }
        )

@router.delete("/tunnels/{tunnel_id}")
async def delete_tunnel(tunnel_id: int, db: Session = Depends(get_db)):
    """
    Elimina un túnel existente
    """
    try:
        tunnel_service = TunnelService(db)
        deleted = await tunnel_service.delete_tunnel(tunnel_id)
        
        if deleted:
            return JSONResponse(content={"success": True})
            
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Túnel no encontrado"}
        )
    except Exception as e:
        logger.error(f"Error eliminando túnel: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/tunnels/{tunnel_id}/start")
async def start_tunnel(tunnel_id: int, db: Session = Depends(get_db)):
    """
    Inicia un túnel específico
    """
    try:
        tunnel_service = TunnelService(db)
        result = await tunnel_service.start_tunnel(tunnel_id)
        return JSONResponse(content={"success": result})
    except Exception as e:
        logger.error(f"Error iniciando túnel {tunnel_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.post("/tunnels/{tunnel_id}/stop")
async def stop_tunnel(tunnel_id: int, db: Session = Depends(get_db)):
    """
    Detiene un túnel específico
    """
    try:
        tunnel_service = TunnelService(db)
        result = await tunnel_service.stop_tunnel(tunnel_id)
        return JSONResponse(content={"success": result})
    except Exception as e:
        logger.error(f"Error deteniendo túnel {tunnel_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/tunnels/{tunnel_id}/status")
async def get_tunnel_status(tunnel_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el estado actual de un túnel
    """
    try:
        tunnel_service = TunnelService(db)
        status = await tunnel_service.get_tunnel_status(tunnel_id)
        return JSONResponse(content={"status": status})
    except Exception as e:
        logger.error(f"Error obteniendo estado del túnel {tunnel_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/tunnels/{tunnel_id}/logs")
async def get_tunnel_logs(
    request: Request,
    tunnel_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Obtiene los logs recientes de un túnel específico
    """
    try:
        tunnel_service = TunnelService(db)
        logs = await tunnel_service.get_tunnel_logs(tunnel_id, limit)
        
        return templates.TemplateResponse(
            "tunnels/logs.html",
            {
                "request": request,
                "tunnel_id": tunnel_id,
                "logs": logs
            }
        )
    except Exception as e:
        logger.error(f"Error obteniendo logs del túnel {tunnel_id}: {str(e)}")
        return templates.TemplateResponse(
            "tunnels/logs.html",
            {
                "request": request,
                "tunnel_id": tunnel_id,
                "logs": [],
                "error": str(e)
            }
        )

@router.get("/tunnels/metrics")
async def get_tunnel_metrics(request: Request, db: Session = Depends(get_db)):
    """
    Obtiene métricas generales de todos los túneles
    """
    try:
        tunnel_service = TunnelService(db)
        metrics = await tunnel_service.get_tunnel_metrics()
        
        return templates.TemplateResponse(
            "tunnels/metrics.html",
            {
                "request": request,
                "metrics": metrics
            }
        )
    except Exception as e:
        logger.error(f"Error obteniendo métricas de túneles: {str(e)}")
        return templates.TemplateResponse(
            "tunnels/metrics.html",
            {
                "request": request,
                "metrics": {},
                "error": str(e)
            }
        )