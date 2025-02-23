# server/app/api/v1/endpoints/dashboard.py
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from sqlalchemy.exc import SQLAlchemyError
from app.services.client_service import ClientService
from app.services.agent_service import AgentService
from app.services.tunnel_service import TunnelService
from app.services.monitor_service import PrinterMonitorService
from datetime import datetime, timedelta
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Endpoint para obtener estadísticas del dashboard con manejo robusto de errores
    
    Returns:
        Un diccionario con estadísticas de clientes, agentes, túneles e impresoras
    """
    try:
        # Servicios 
        services = {
            "client": ClientService(db),
            "agent": AgentService(db),
            "tunnel": TunnelService(db),
            "printer": PrinterMonitorService(db)
        }

        # Estructura de estadísticas predeterminada
        stats = {
            "printers": {
                "total": 0,
                "online": 0,
                "offline": 0,
                "error": 0,
                "last_updated": datetime.now().isoformat()
            },
            "clients": {
                "total": 0,
                "active": 0,
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
            }
        }

        # Obtener estadísticas de clientes
        try:
            clients = services["client"].get_all()
            recent_threshold = datetime.now() - timedelta(days=30)
            stats["clients"]["total"] = len(clients)
            stats["clients"]["active"] = len([
                c for c in clients 
                if getattr(c, 'is_active', False) or 
                   (getattr(c, 'created_at', datetime.min) > recent_threshold)
            ])
        except Exception as e:
            logger.warning(f"Error en estadísticas de clientes: {str(e)}")

        # Obtener estadísticas de agentes
        try:
            agents = services["agent"].get_all()
            stats["agents"]["total"] = len(agents)
            stats["agents"]["online"] = len([
                a for a in agents 
                if getattr(a, 'status', '').lower() == 'online'
            ])
            stats["agents"]["offline"] = stats["agents"]["total"] - stats["agents"]["online"]
        except Exception as e:
            logger.warning(f"Error en estadísticas de agentes: {str(e)}")

        # Obtener estadísticas de túneles
        try:
            tunnels = services["tunnel"].get_all()
            stats["tunnels"]["total"] = len(tunnels)
            stats["tunnels"]["active"] = len([
                t for t in tunnels 
                if getattr(t, 'status', '').lower() == 'active'
            ])
        except Exception as e:
            logger.warning(f"Error en estadísticas de túneles: {str(e)}")

        # Obtener estadísticas de impresoras
        try:
            printers = services["printer"].get_all()
            stats["printers"]["total"] = len(printers)
            stats["printers"]["online"] = len([
                p for p in printers 
                if getattr(p, 'status', '').lower() == 'online'
            ])
            stats["printers"]["offline"] = len([
                p for p in printers 
                if getattr(p, 'status', '').lower() == 'offline'
            ])
            stats["printers"]["error"] = len([
                p for p in printers 
                if getattr(p, 'status', '').lower() == 'error'
            ])
        except Exception as e:
            logger.warning(f"Error en estadísticas de impresoras: {str(e)}")

        return stats

    except SQLAlchemyError as e:
        logger.error(f"Error de base de datos: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Error al cargar estadísticas de base de datos"
        )
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Error interno al procesar estadísticas"
        )