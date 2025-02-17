# server/app/api/v1/api.py
from fastapi import APIRouter, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from app.api.v1.endpoints import (
    agents, websocket, web, printers, drivers,
    tunnels, monitor_printers, printer_oids,
    dashboard, auth, users
)

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.scheme == "https" and not request.base_url.hostname == "localhost":
            https_url = str(request.url.replace(scheme="https"))
            return RedirectResponse(https_url, status_code=301)
        return await call_next(request)

# Definición de routers principales
api_router = APIRouter()
web_router = APIRouter()

# Configuración de CORS para el API router
api_router.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Rutas para websocket con manejo seguro
api_router.include_router(
    websocket.router,
    prefix="/ws",
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

# Middleware para forzar HTTPS
api_router.middleware("http")(HTTPSRedirectMiddleware())

# Handler para errores de WebSocket
@api_router.websocket_route("/ws/{path:path}")
async def websocket_catch_all(websocket):
    try:
        await websocket.accept()
        await websocket.send_json({"error": "Invalid WebSocket path"})
    finally:
        await websocket.close()

# Verificador de esquema HTTPS
@api_router.middleware("http")
async def verify_https(request: Request, call_next):
    if request.url.scheme != "https" and not request.base_url.hostname == "localhost":
        return RedirectResponse(
            url=str(request.url.replace(scheme="https")),
            status_code=301
        )
    return await call_next(request)