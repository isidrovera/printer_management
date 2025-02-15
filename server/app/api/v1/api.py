# server/app/api/v1/api.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.api.v1.endpoints import (
    agents, websocket, web, printers, drivers,
    tunnels, monitor_printers, printer_oids,
    dashboard, auth, users
)
from app.core.config import settings

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

# Rutas de WebSocket - Movido al principio para priorizar
api_router.include_router(
    websocket.router,
    prefix="/ws",  # Cambiado de /wss a /ws
    tags=["websocket"]
)

# Resto de rutas API
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
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

# Manejador de errores global
@api_router.exception_handler(Exception)
async def global_exception_handler(request, exc):
    error_msg = str(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": error_msg}
    )

# Healthcheck endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.VERSION}