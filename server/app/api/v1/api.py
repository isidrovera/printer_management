# server/app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
    agents,
    websocket,
    printers,
    drivers,
    tunnels,
    monitor_printers,
    printer_oids
)
from app.api.v1.endpoints.web import router as web_router

# Router principal para APIs
api_router = APIRouter()

# Rutas de API
api_router.include_router(
    drivers.router, 
    prefix="/drivers", 
    tags=["drivers"]
)

api_router.include_router(
    agents.router, 
    prefix="/agents", 
    tags=["agents"]
)

api_router.include_router(
    websocket.router, 
    prefix="/ws", 
    tags=["websocket"]
)

api_router.include_router(
    printers.router, 
    prefix="/printers", 
    tags=["printers"]
)

api_router.include_router(
    tunnels.router, 
    prefix="/tunnels", 
    tags=["tunnels"]
)

api_router.include_router(
    monitor_printers.router, 
    prefix="/monitor/printers", 
    tags=["monitor_printers"]
)

api_router.include_router(
    printer_oids.router, 
    prefix="/printer-oids", 
    tags=["printer-oids"]
)

# Router web separado
web_router = APIRouter()
web_router.include_router(
    web_router,  # Este es el router que importamos de web/__init__.py
    tags=["web"]
)