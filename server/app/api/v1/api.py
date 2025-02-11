# server/app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
   agents, websocket, web, printers, drivers,
   tunnels, monitor_printers, printer_oids,
   dashboard, auth, users
)
# Rutas para usuarios
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)
# Routers principales
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