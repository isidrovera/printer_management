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

@router.post("/create", response_model=TunnelResponse)
async def create_tunnel(
    tunnel_data: TunnelCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuevo túnel SSH."""
    tunnel_service = TunnelService(db)
    return await tunnel_service.create_tunnel(tunnel_data)
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

@router.post("/create", response_model=TunnelResponse)
async def create_tunnel(
    tunnel_data: TunnelCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuevo túnel SSH."""
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