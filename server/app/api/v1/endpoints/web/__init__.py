#server\app\api\v1\endpoints\web\__init__.py
from fastapi import APIRouter
from . import dashboard, clients, agents, drivers, tunnels, monitor_printers, printer_oids

router = APIRouter()

# Incluir todos los routers web
router.include_router(dashboard.router)
router.include_router(clients.router)
router.include_router(agents.router)
router.include_router(drivers.router)
router.include_router(tunnels.router)
router.include_router(monitor_printers.router)
router.include_router(printer_oids.router)

__all__ = ["router"]