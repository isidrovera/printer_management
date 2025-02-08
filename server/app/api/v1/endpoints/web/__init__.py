#server\app\api\v1\endpoints\web\__init__.py

from fastapi import APIRouter
from . import dashboard, clients, agents, drivers, tunnels, monitor_printers, printer_oids

# Crear router principal para web
router = APIRouter()

# Incluir todas las rutas web
router.include_router(dashboard.router)  # Ruta raíz '/'
router.include_router(clients.router)    # Rutas /clients/*
router.include_router(agents.router)     # Rutas /agents/*
router.include_router(drivers.router)    # Rutas /drivers/*
router.include_router(tunnels.router)    # Rutas /tunnels/*
router.include_router(monitor_printers.router)  # Rutas /monitor/printers/*
router.include_router(printer_oids.router)      # Rutas /printer-oids/*

# Exportar el router web
__all__ = ["router"]