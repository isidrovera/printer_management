# server/app/api/v1/endpoints/web.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from sqlalchemy.exc import SQLAlchemyError

from app.services.client_service import ClientService
from app.services.agent_service import AgentService
from app.services.driver_service import DriverService
from app.services.tunnel_service import TunnelService
from app.services.monitor_service import PrinterMonitorService
from fastapi import File, UploadFile
from pathlib import Path
from app.core.config import settings
from fastapi.responses import FileResponse
from fastapi import HTTPException
from datetime import datetime

import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
@router.get("/clients")
async def list_clients(request: Request, db: Session = Depends(get_db)):
    client_service = ClientService(db)
    clients = await client_service.get_all()
    return templates.TemplateResponse(
        "clients/list.html",
        {"request": request, "clients": clients}
    )

@router.get("/clients/create")
async def create_client_form(request: Request):
    return templates.TemplateResponse(
        "clients/form.html",
        {"request": request, "client": None}
    )

@router.get("/clients/{client_id}/edit")
async def edit_client_form(request: Request, client_id: int, db: Session = Depends(get_db)):
    client_service = ClientService(db)
    client = await client_service.get_by_id(client_id)
    return templates.TemplateResponse(
        "clients/form.html",
        {"request": request, "client": client}
    )
@router.post("/clients/{client_id}/edit")
async def edit_client(request: Request, client_id: int, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        name = form.get("name")
        logger.info(f"Editing client with ID {client_id}, new name: {name}")

        client_service = ClientService(db)
        client = await client_service.get_by_id(client_id)

        if not client:
            return templates.TemplateResponse(
                "clients/form.html",
                {"request": request, "client": None, "error": "Cliente no encontrado"}
            )

        await client_service.update(client_id, name=name)
        logger.info(f"Client with ID {client_id} updated successfully")
        return RedirectResponse("/clients", status_code=303)
    except Exception as e:
        logger.error(f"Error editing client: {str(e)}")
        return templates.TemplateResponse(
            "clients/form.html",
            {"request": request, "client": {"id": client_id, "name": form.get("name")}, "error": str(e)}
        )

@router.post("/clients/create")
async def create_client(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        name = form.get("name")
        logger.info(f"Creating client with name: {name}")
        
        client_service = ClientService(db)
        await client_service.create(name=name)
        
        logger.info("Client created successfully")
        return RedirectResponse("/clients", status_code=303)
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        return templates.TemplateResponse(
            "clients/form.html",
            {"request": request, "client": None, "error": str(e)}
        )

@router.delete("/clients/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    try:
        client_service = ClientService(db)
        deleted = await client_service.delete(client_id)
        if deleted:
            return {"success": True}
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Cliente no encontrado"}
        )
    except Exception as e:
        logger.error(f"Error eliminando cliente: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/agents")
async def list_agents(request: Request, db: Session = Depends(get_db)):
    agent_service = AgentService(db)
    agents = await agent_service.get_agents(skip=0, limit=100)
    print(f"Agentes obtenidos: {agents}")  # Debug
    drivers = await agent_service.get_drivers()
    print(f"Drivers obtenidos: {drivers}")  # Debug
    return templates.TemplateResponse(
        "agents/agents.html",
        {"request": request, "agents": agents, "drivers": drivers}
    )




# Cambiar la ruta de la vista de drivers
@router.get("/drivers")  # Cambiado de /drivers a /drivers-view
async def list_drivers(request: Request, db: Session = Depends(get_db)):
   driver_service = DriverService(db)
   drivers = await driver_service.get_all()
   return templates.TemplateResponse("drivers/list.html", {
       "request": request,
       "drivers": drivers
   })

@router.get("/drivers/create")  # Actualizado
async def create_driver_form(request: Request):
   return templates.TemplateResponse("drivers/form.html", {
       "request": request,
       "driver": None
   })

@router.post("/drivers/create")
async def create_driver(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        driver_file: UploadFile = form.get("driver_file")
        if not driver_file:
            raise ValueError("Se requiere archivo de driver")

        # Leer el archivo como binario
        file_content = await driver_file.read()
        filename = driver_file.filename  # Obtener el nombre original del archivo

        # Guardar el archivo y registrar el driver en la base de datos
        driver_service = DriverService(db)
        driver = await driver_service.create_driver(
            manufacturer=form.get("manufacturer"),
            model=form.get("model"),
            driver_file=file_content,
            filename=filename,
            description=form.get("description")
        )

        logger.info(f"Driver creado: {driver.manufacturer} {driver.model}")
        return RedirectResponse("/drivers", status_code=303)
    except Exception as e:
        logger.error(f"Error creando driver: {str(e)}")
        return templates.TemplateResponse(
            "drivers/form.html",
            {"request": request, "driver": None, "error": str(e)}
        )



@router.get("/drivers/{driver_id}/edit")
async def edit_driver_form(request: Request, driver_id: int, db: Session = Depends(get_db)):
   driver_service = DriverService(db)
   driver = await driver_service.get_by_id(driver_id)
   if not driver:
       return RedirectResponse("/drivers", status_code=303)
   return templates.TemplateResponse("drivers/form.html", {
       "request": request,
       "driver": driver
   })

@router.post("/drivers/{driver_id}/edit") 
async def edit_driver(request: Request, driver_id: int, db: Session = Depends(get_db)):
   try:
       form = await request.form()
       driver_service = DriverService(db)

       driver = await driver_service.update(
           driver_id,
           manufacturer=form.get("manufacturer"),
           model=form.get("model"),
           description=form.get("description")
       )
       
       logger.info(f"Driver actualizado: {driver.manufacturer} {driver.model}")
       return RedirectResponse("/drivers", status_code=303)
   except Exception as e:
       logger.error(f"Error actualizando driver: {str(e)}")
       return templates.TemplateResponse(
           "drivers/form.html",
           {"request": request, "driver_id": driver_id, "error": str(e)}
       )

@router.delete("/drivers/{driver_id}")
async def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    try:
        driver_service = DriverService(db)
        driver = await driver_service.get_by_id(driver_id)
        if not driver:
            return {"success": False, "error": "Driver no encontrado"}, 404
            
        deleted = await driver_service.delete_driver(driver_id)  # ← Método corregido
        return {"success": True} if deleted else {"success": False, "error": "Error al eliminar"}
    except Exception as e:
        logger.error(f"Error eliminando driver: {str(e)}")
        return {"success": False, "error": str(e)}



@router.get("/drivers/{driver_id}/download")
async def download_driver(driver_id: int, db: Session = Depends(get_db)):
    driver_service = DriverService(db)
    driver = await driver_service.get_by_id(driver_id)
    
    if not driver:
        return JSONResponse(
            status_code=404,
            content={"error": "Driver no encontrado"}
        )

    # Usar configuración correcta del almacenamiento
    file_path = Path(settings.DRIVERS_STORAGE_PATH) / driver.driver_filename

    if not file_path.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "Archivo no encontrado"}
        )

    return FileResponse(path=file_path, filename=driver.driver_filename, media_type="application/octet-stream")




@router.get("/tunnels")
async def list_tunnels_view(request: Request, db: Session = Depends(get_db)):
    tunnel_service = TunnelService(db)
    tunnels = await tunnel_service.list_tunnels()
    return templates.TemplateResponse(
        "tunnels/list.html",  # This will use the template we created
        {
            "request": request,
            "tunnels": tunnels
        }
    )




@router.get("/monitor/printers")
async def list_printers(request: Request, db: Session = Depends(get_db)):
    """
    Vista para listar todas las impresoras monitoreadas
    """
    try:
        printer_service = PrinterMonitorService(db)
        
        # Generar un informe de impresoras
        report = printer_service.generate_printer_report()
        
        # Obtener todas las impresoras con consumibles críticos
        critical_printers = printer_service.get_printers_with_critical_supplies()
        
        return templates.TemplateResponse(
            "monitor_printers.html",  # El nombre de su template
            {
                "request": request, 
                "printers": critical_printers,
                "stats": {
                    "total": len(critical_printers),
                    "online": len([p for p in critical_printers if p.status == 'online']),
                    "error": len([p for p in critical_printers if p.status == 'error'])
                }
            }
        )
    except Exception as e:
        logger.error(f"Error en monitor de impresoras: {str(e)}")
        return templates.TemplateResponse(
            "monitor_printers.html",
            {
                "request": request, 
                "printers": [],
                "error": str(e)
            }
        )
@router.get("/printers/{printer_id}")
async def printer_details(request: Request, printer_id: int, db: Session = Depends(get_db)):
    """
    Vista de detalles de una impresora específica
    """
    try:
        printer_service = PrinterMonitorService(db)
        
        # Obtener detalles de la impresora
        printer = db.query(Printer).filter(Printer.id == printer_id).first()
        
        if not printer:
            return templates.TemplateResponse(
                "printers/not_found.html",
                {"request": request, "printer_id": printer_id}
            )
        
        # Obtener historial de los últimos 7 días
        history = printer_service.get_printer_history(printer_id)
        
        # Obtener consumibles críticos
        critical_supplies = printer.check_critical_supplies()
        
        return templates.TemplateResponse(
            "printers/details.html",
            {
                "request": request, 
                "printer": printer,
                "history": history,
                "critical_supplies": critical_supplies
            }
        )
    except Exception as e:
        logger.error(f"Error obteniendo detalles de impresora {printer_id}: {str(e)}")
        return templates.TemplateResponse(
            "printers/details.html",
            {
                "request": request, 
                "printer": None,
                "error": str(e)
            }
        )

@router.get("/printers/report")
async def printer_report(request: Request, db: Session = Depends(get_db)):
    """
    Vista de informe general de impresoras
    """
    try:
        printer_service = PrinterMonitorService(db)
        report = printer_service.generate_printer_report()
        
        return templates.TemplateResponse(
            "printers/report.html",
            {
                "request": request, 
                "report": report
            }
        )
    except Exception as e:
        logger.error(f"Error generando informe de impresoras: {str(e)}")
        return templates.TemplateResponse(
            "printers/report.html",
            {
                "request": request, 
                "report": {},
                "error": str(e)
            }
        )