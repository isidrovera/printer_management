# server/app/api/v1/api.py
from fastapi import APIRouter

# Router para APIs
api_router = APIRouter()

# Importar routers individuales
from app.api.v1.endpoints import dashboard  # Nuevo import para dashboard
from app.api.v1.endpoints import agents
from app.api.v1.endpoints import websocket
from app.api.v1.endpoints import printers
from app.api.v1.endpoints import drivers
from app.api.v1.endpoints import tunnels
from app.api.v1.endpoints import monitor_printers
from app.api.v1.endpoints import printer_oids
from app.api.v1.endpoints import clients     # Nuevo import para clients

# Incluir primero las rutas web principales
api_router.include_router(
    dashboard.router,
    tags=["dashboard"]
)

api_router.include_router(
    clients.router,
    prefix="/clients",
    tags=["clients"]
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