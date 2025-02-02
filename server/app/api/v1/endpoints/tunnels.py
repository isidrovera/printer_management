# server/app/api/v1/endpoints/tunnels.py
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from typing import Optional, Dict
from ....db.session import get_db
from ....services.tunnel_service import TunnelService
from ....schemas.tunnel import TunnelCreate, TunnelResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/create")
async def create_tunnel(tunnel_data: TunnelCreate, db: Session = Depends(get_db)):
    logger.debug(f"Received tunnel data: {tunnel_data}")  # Agregar logging
    tunnel_service = TunnelService(db)
    return await tunnel_service.create_tunnel(tunnel_data)

@router.delete("/{tunnel_id}")
async def close_tunnel(
    tunnel_id: str,
    db: Session = Depends(get_db)
):
    """Cierra un túnel SSH existente."""
    tunnel_service = TunnelService(db)
    return await tunnel_service.close_tunnel(tunnel_id)

@router.get("/list")
async def list_tunnels(
    db: Session = Depends(get_db)
):
    """Lista todos los túneles activos."""
    tunnel_service = TunnelService(db)
    return await tunnel_service.list_tunnels()
@router.delete("/{tunnel_id}")
async def close_tunnel(
    tunnel_id: str,
    db: Session = Depends(get_db)
):
    """Cierra un túnel SSH existente."""
    tunnel_service = TunnelService(db)
    return await tunnel_service.close_tunnel(tunnel_id)

@router.get("/list")
async def list_tunnels(
    db: Session = Depends(get_db)
):
    """Lista todos los túneles activos."""
    tunnel_service = TunnelService(db)
    return await tunnel_service.list_tunnels()
    
    
    
    
@router.get("/{tunnel_id}")
async def get_tunnel_info(
    tunnel_id: str,
    db: Session = Depends(get_db)
):
    """Obtiene información detallada de un túnel específico."""
    try:
        logger.debug(f"Obteniendo información del túnel: {tunnel_id}")
        tunnel_service = TunnelService(db)
        tunnel = await tunnel_service.get_tunnel_info(tunnel_id)
        
        if not tunnel:
            raise HTTPException(status_code=404, detail="Túnel no encontrado")
            
        return tunnel
    except Exception as e:
        logger.error(f"Error obteniendo información del túnel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))