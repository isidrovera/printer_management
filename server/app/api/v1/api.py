# server/app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
    agents, websocket, web, printers, drivers,
    tunnels, monitor_printers, printer_oids,
    dashboard, auth, users
)

# Definición de routers principales
api_router = APIRouter()
web_router = APIRouter()

# Router web y autenticación
web_router.include_router(
    web.router,
    tags=["web"]
)

web_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

# Rutas de API
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"]
)

# Rutas para usuarios
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# Rutas para drivers
api_router.include_router(
    drivers.router,
    prefix="/drivers",
    tags=["drivers"]
)

# Rutas para agentes
api_router.include_router(
    agents.router,
    prefix="/agents", 
    tags=["agents"]
)

# Rutas para websocket
api_router.include_router(
    websocket.router,
    prefix="/wss",
    tags=["websocket"]
)

# Rutas para impresoras
api_router.include_router(
    printers.router,
    prefix="/printers",
    tags=["printers"]
)

# Rutas para túneles
api_router.include_router(
    tunnels.router,
    prefix="/tunnels",
    tags=["tunnels"]
)

# Rutas para monitoreo de impresoras
api_router.include_router(
    monitor_printers.router,
    prefix="/monitor/printers",
    tags=["monitor_printers"]
)

# Rutas para OIDs de impresoras
api_router.include_router(
    printer_oids.router,
    prefix="/printer-oids",
    tags=["printer-oids"]
)