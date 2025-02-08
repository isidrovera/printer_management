#server\app\api\v1\endpoints\web\__init__.py
# Exportar todos los módulos
from . import (
    dashboard,
    agents,
    websocket,
    printers,
    drivers,
    tunnels,
    monitor_printers,
    printer_oids,
    clients
)

__all__ = [
    "dashboard",
    "agents",
    "websocket",
    "printers",
    "drivers",
    "tunnels",
    "monitor_printers",
    "printer_oids",
    "clients"
]