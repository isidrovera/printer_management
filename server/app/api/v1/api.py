#printer_management\server\app\api\v1\api.py
from fastapi import APIRouter
from app.api.v1.endpoints import agents, websocket, web, printers, drivers

api_router = APIRouter()

# Los prefijos son relativos a /api/v1
api_router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(printers.router, prefix="/printers", tags=["printers"])
api_router.include_router(web.router, tags=["web"])