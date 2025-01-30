# server/app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import agents, websocket, web, printers, drivers, tunnels

# Router para APIs
api_router = APIRouter()
api_router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])  # /api/v1/ws
api_router.include_router(printers.router, prefix="/printers", tags=["printers"])
api_router.include_router(tunnels.router, prefix="/tunnels", tags=["tunnels"])
# Router web separado
web_router = APIRouter()
web_router.include_router(web.router, tags=["web"])