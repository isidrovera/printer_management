# server/app/api/v1/endpoints/dashboard.py
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from sqlalchemy.exc import SQLAlchemyError
from app.services.client_service import ClientService
from app.services.agent_service import AgentService
from app.services.tunnel_service import TunnelService
from app.services.monitor_service import PrinterMonitorService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint que devuelve las estadísticas para el dashboard
    """
    try:
        # Inicializar servicios
        client_service = ClientService(db)
        agent_service = AgentService(db)
        tunnel_service = TunnelService(db)

        # Obtener estadísticas básicas
        stats = {
            "clients": {
                "total": len(client_service.get_all()) if hasattr(client_service, 'get_all') else 0,
                "last_updated": datetime.now().isoformat()
            },
            "agents": {
                "total": 0,
                "online": 0,
                "offline": 0,
                "last_updated": datetime.now().isoformat()
            },
            "tunnels": {
                "total": 0,
                "active": 0,
                "last_updated": datetime.now().isoformat()
            },
            "printers": {
                "total": 0,
                "online": 0,
                "offline": 0,
                "last_updated": datetime.now().isoformat()
            }
        }

        # Intentar obtener estadísticas de agentes
        try:
            agents = agent_service.get_all() if hasattr(agent_service, 'get_all') else []
            stats["agents"]["total"] = len(agents)
            stats["agents"]["online"] = len([a for a in agents if getattr(a, 'status', None) == 'online'])
            stats["agents"]["offline"] = stats["agents"]["total"] - stats["agents"]["online"]
        except Exception as e:
            logger.warning(f"Error al obtener estadísticas de agentes: {str(e)}")

        # Intentar obtener estadísticas de túneles
        try:
            tunnels = tunnel_service.get_all() if hasattr(tunnel_service, 'get_all') else []
            stats["tunnels"]["total"] = len(tunnels)
            stats["tunnels"]["active"] = len([t for t in tunnels if getattr(t, 'status', None) == 'active'])
        except Exception as e:
            logger.warning(f"Error al obtener estadísticas de túneles: {str(e)}")

        # Intentar obtener estadísticas de impresoras
        try:
            printer_service = PrinterMonitorService(db)
            printers = printer_service.get_all() if hasattr(printer_service, 'get_all') else []
            stats["printers"]["total"] = len(printers)
            stats["printers"]["online"] = len([p for p in printers if getattr(p, 'status', None) == 'online'])
            stats["printers"]["offline"] = stats["printers"]["total"] - stats["printers"]["online"]
        except Exception as e:
            logger.warning(f"Error al obtener estadísticas de impresoras: {str(e)}")

        return stats

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error de base de datos al cargar estadísticas"
        )
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error inesperado al cargar estadísticas"
        )