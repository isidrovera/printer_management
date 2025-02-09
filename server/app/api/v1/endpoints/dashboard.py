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
    logger.info("Iniciando carga de estadísticas del dashboard")
    
    try:
        # Inicializar servicios
        logger.debug("Inicializando servicios necesarios")
        client_service = ClientService(db)
        agent_service = AgentService(db)
        tunnel_service = TunnelService(db)
        
        # Estadísticas de clientes
        logger.debug("Obteniendo estadísticas de clientes")
        clients_total = client_service.get_count()
        logger.info(f"Total de clientes: {clients_total}")

        # Estadísticas de agentes
        logger.debug("Obteniendo estadísticas de agentes")
        agents_total = agent_service.get_count()
        agents_online = agent_service.get_count_by_status("online")
        logger.info(f"Agentes - Total: {agents_total}, Online: {agents_online}")

        # Estadísticas de túneles
        logger.debug("Obteniendo estadísticas de túneles")
        tunnels_total = tunnel_service.get_count()
        tunnels_active = tunnel_service.get_count_by_status("active")
        logger.info(f"Túneles - Total: {tunnels_total}, Activos: {tunnels_active}")

        stats = {
            "clients": {
                "total": clients_total,
                "last_updated": datetime.now().isoformat()
            },
            "agents": {
                "total": agents_total,
                "online": agents_online,
                "offline": agents_total - agents_online,
                "last_updated": datetime.now().isoformat()
            },
            "tunnels": {
                "total": tunnels_total,
                "active": tunnels_active,
                "last_updated": datetime.now().isoformat()
            }
        }

        # Intentar obtener estadísticas de impresoras si el servicio está disponible
        try:
            printer_service = PrinterMonitorService(db)
            printers_total = printer_service.get_count()
            printers_online = printer_service.get_count_by_status("online")
            
            stats["printers"] = {
                "total": printers_total,
                "online": printers_online,
                "offline": printers_total - printers_online,
                "last_updated": datetime.now().isoformat()
            }
            logger.info(f"Impresoras - Total: {printers_total}, Online: {printers_online}")
        except Exception as e:
            logger.warning("Servicio de impresoras no disponible", exc_info=True)
            stats["printers"] = {
                "total": 0,
                "online": 0,
                "offline": 0,
                "service_unavailable": True,
                "last_updated": datetime.now().isoformat()
            }

        return stats

    except SQLAlchemyError as e:
        logger.error("Error de base de datos al cargar estadísticas", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error de base de datos al cargar estadísticas"
        )
    except Exception as e:
        logger.error("Error inesperado al cargar estadísticas", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error inesperado al cargar estadísticas"
        )