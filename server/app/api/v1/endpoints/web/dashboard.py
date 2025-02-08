from fastapi import APIRouter, Request, Depends
from typing import Optional
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db
from sqlalchemy.exc import SQLAlchemyError
from app.services.client_service import ClientService
from app.services.agent_service import AgentService
from app.services.tunnel_service import TunnelService
from datetime import datetime

import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Mantener los mismos filtros que en el archivo original
templates.env.filters['numberformat'] = lambda value: "{:,}".format(value)
templates.env.filters['default'] = lambda value, default_value: value if value is not None else default_value

@router.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint principal que muestra el dashboard con estadísticas.
    """
    start_time = datetime.now()
    logger.info("Iniciando carga del dashboard")
    
    try:
        # Inicializar servicios
        logger.debug("Inicializando servicios necesarios")
        client_service = ClientService(db)
        agent_service = AgentService(db)
        tunnel_service = TunnelService(db)
        
        # Si no existe PrinterService, podemos omitir esas estadísticas
        try:
            printer_service = PrinterService(db)
            has_printer_service = True
            logger.debug("Servicio de impresoras inicializado correctamente")
        except NameError:
            has_printer_service = False
            logger.warning("PrinterService no está disponible, omitiendo estadísticas de impresoras")

        # Obtener estadísticas de clientes
        logger.debug("Obteniendo estadísticas de clientes")
        total_clients = await client_service.get_count()
        logger.info(f"Total de clientes obtenidos: {total_clients}")

        # Obtener estadísticas de agentes
        logger.debug("Obteniendo estadísticas de agentes")
        agents_total = await agent_service.get_count()
        agents_online = await agent_service.get_count_by_status("online")
        agents_offline = await agent_service.get_count_by_status("offline")
        logger.info(f"Estadísticas de agentes - Total: {agents_total}, Online: {agents_online}, Offline: {agents_offline}")

        # Obtener estadísticas de túneles
        logger.debug("Obteniendo estadísticas de túneles")
        tunnels_total = await tunnel_service.get_count()
        tunnels_active = await tunnel_service.get_count_by_status("active")
        logger.info(f"Estadísticas de túneles - Total: {tunnels_total}, Activos: {tunnels_active}")

        # Construir diccionario base de estadísticas
        stats = {
            "total_clients": total_clients,
            "agents": {
                "total": agents_total,
                "online": agents_online,
                "offline": agents_offline
            },
            "tunnels": {
                "total": tunnels_total,
                "active": tunnels_active
            },
            "last_updated": datetime.now().isoformat()
        }

        # Agregar estadísticas de impresoras solo si el servicio está disponible
        if has_printer_service:
            logger.debug("Obteniendo estadísticas de impresoras")
            printers_total = await printer_service.get_count()
            printers_online = await printer_service.get_count_by_status("online")
            logger.info(f"Estadísticas de impresoras - Total: {printers_total}, Online: {printers_online}")
            
            stats["printers"] = {
                "total": printers_total,
                "online": printers_online
            }
        else:
            stats["printers"] = {
                "total": 0,
                "online": 0,
                "service_unavailable": True
            }

        # Calcular tiempo de ejecución
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Dashboard cargado exitosamente en {execution_time:.2f} segundos")

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "stats": stats
            }
        )

    except SQLAlchemyError as e:
        logger.error("Error de base de datos al cargar el dashboard")
        logger.exception(e)
        return handle_dashboard_error(request, "Error de base de datos al cargar estadísticas")

    except Exception as e:
        logger.error("Error inesperado al cargar el dashboard")
        logger.exception(e)
        return handle_dashboard_error(request, "Error inesperado al cargar estadísticas")

def handle_dashboard_error(request: Request, error_message: str = "Error al cargar estadísticas"):
    """
    Maneja los errores del dashboard retornando una respuesta con estadísticas en 0.
    """
    logger.info(f"Retornando respuesta de error: {error_message}")
    stats = {
        "total_clients": 0,
        "agents": {"total": 0, "online": 0, "offline": 0},
        "tunnels": {"total": 0, "active": 0},
        "printers": {"total": 0, "online": 0},
        "last_updated": datetime.now().isoformat(),
        "error": True
    }
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "stats": stats,
            "error": error_message
        }
    )