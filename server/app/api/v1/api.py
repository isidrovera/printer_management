# server/app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
    agents, websocket, printers, drivers,
    tunnels, monitor_printers, printer_oids,
    dashboard, auth, users, clients
)

# Main API router definition
api_router = APIRouter()

# Auth routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)

# Dashboard routes
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"]
)
api_router.include_router(
    clients.router,
    prefix="/clients",
    tags=["clients"]
)
# User routes
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# Driver routes
api_router.include_router(
    drivers.router,
    prefix="/drivers",
    tags=["drivers"]
)

# Agent routes
api_router.include_router(
    agents.router,
    prefix="/agents", 
    tags=["agents"]
)

# WebSocket routes
api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["websocket"]
)

# Printer routes
api_router.include_router(
    printers.router,
    prefix="/printers",
    tags=["printers"]
)

# Tunnel routes
api_router.include_router(
    tunnels.router,
    prefix="/tunnels",
    tags=["tunnels"]
)

# Printer monitoring routes
api_router.include_router(
    monitor_printers.router,
    prefix="/monitor/printers",
    tags=["monitor_printers"]
)

# Printer OIDs routes
api_router.include_router(
    printer_oids.router,
    prefix="/printer-oids",
    tags=["printer-oids"]
)