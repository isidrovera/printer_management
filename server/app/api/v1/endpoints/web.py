# server/app/api/v1/endpoints/web.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import joinedload
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from sqlalchemy.exc import SQLAlchemyError
from app.services.printer_oids import PrinterOIDsService
from fastapi.responses import JSONResponse
from app.services.client_service import ClientService
from app.services.agent_service import AgentService
from app.services.driver_service import DriverService
from app.services.tunnel_service import TunnelService
from app.services.monitor_service import PrinterMonitorService
from app.db.models.printer import Printer
from app.db.models.client import Client
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
# Agregar estos filtros después de la declaración de templates
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

templates.env.filters['numberformat'] = lambda value: "{:,}".format(value)


@router.get("/monitor/printers")
async def list_printers(request: Request, db: Session = Depends(get_db)):
    try:
        logger.info("Iniciando listado de impresoras")
        # Cargar impresoras con sus clientes
        printers = db.query(Printer).options(joinedload(Printer.client)).all()
        
        # Obtener lista de clientes
        client_service = ClientService(db)
        clients = await client_service.get_all()
        
        processed_printers = []
        for printer in printers:
            try:
                # Log de depuración para el cliente
                logger.debug(f"Impresora ID: {printer.id}")
                logger.debug(f"Cliente asociado: {printer.client}")
                logger.debug(f"Nombre del cliente: {printer.client.name if printer.client else 'Sin cliente'}")

                printer_data = printer.printer_data or {}
                supplies = printer_data.get('supplies', {})
                toners = supplies.get('toners', {})
                
                printer_info = {
                    'id': printer.id,
                    'name': printer.name,
                    'brand': printer.brand,
                    'model': printer.model,
                    'ip_address': printer.ip_address,
                    'status': printer.status,
                    'client': printer.client.name if printer.client else 'Sin cliente',
                    'has_alerts': False,
                    'supplies': {
                        'black': {'level': toners.get('black', {}).get('percentage', 0)},
                        'cyan': {'level': toners.get('cyan', {}).get('percentage', 0)},
                        'magenta': {'level': toners.get('magenta', {}).get('percentage', 0)},
                        'yellow': {'level': toners.get('yellow', {}).get('percentage', 0)}
                    },
                    'counters': {
                        'total': printer_data.get('counters', {}).get('total', 0)
                    }
                }
                
                try:
                    printer_info['has_alerts'] = bool(printer.check_critical_supplies())
                except Exception as e:
                    logger.warning(f"Error verificando suministros críticos para impresora {printer.id}: {e}")

                processed_printers.append(printer_info)
                
            except Exception as e:
                logger.error(f"Error procesando impresora {printer.id}: {str(e)}")
                continue

        return templates.TemplateResponse(
            "monitor/monitor_printers.html",
            {
                "request": request,
                "printers": processed_printers,
                "clients": clients,
                "stats": {
                    "total": len(processed_printers),
                    "online": len([p for p in processed_printers if p['status'] == 'online']),
                    "error": len([p for p in processed_printers if p['status'] == 'error'])
                }
            }
        )
    except Exception as e:
        logger.error(f"Error general en list_printers: {str(e)}")
        return templates.TemplateResponse(
            "monitor/monitor_printers.html",
            {
                "request": request,
                "printers": [],
                "clients": [],
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
        
        
        
        
@router.get("/printer-oids")
async def list_printer_oids(request: Request, db: Session = Depends(get_db)):
    try:
        printer_oids_service = PrinterOIDsService(db)
        oids = printer_oids_service.get_all()
        return templates.TemplateResponse(
            "printer_oids/list.html",
            {"request": request, "printer_oids": oids}
        )
    except Exception as e:
        logger.error(f"Error listing printer OIDs: {str(e)}")
        return templates.TemplateResponse(
            "printer_oids/list.html",
            {"request": request, "printer_oids": [], "error": str(e)}
        )

@router.get("/printer-oids/create")
async def create_printer_oids_form(request: Request):
    return templates.TemplateResponse(
        "printer_oids/form.html",
        {"request": request, "printer_oids": None}
    )

@router.post("/printer-oids/create")
async def create_printer_oids(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        
        # Crear diccionario con los datos del formulario
        oid_data = {
            "brand": form.get("brand"),
            "model_family": form.get("model_family"),
            "description": form.get("description"),
            "oid_total_pages": form.get("oid_total_pages"),
            "oid_total_color_pages": form.get("oid_total_color_pages"),
            "oid_black_toner_level": form.get("oid_black_toner_level"),
            "oid_cyan_toner_level": form.get("oid_cyan_toner_level"),
            "oid_magenta_toner_level": form.get("oid_magenta_toner_level"),
            "oid_yellow_toner_level": form.get("oid_yellow_toner_level")
        }
        
        printer_oids_service = PrinterOIDsService(db)
        # Verificar si ya existe una configuración para esta marca y familia
        existing = printer_oids_service.get_by_brand_and_family(
            oid_data["brand"],
            oid_data["model_family"]
        )
        
        if existing:
            return templates.TemplateResponse(
                "printer_oids/form.html",
                {
                    "request": request,
                    "printer_oids": None,
                    "error": "Ya existe una configuración para esta marca y familia de modelos"
                }
            )
        
        await printer_oids_service.create(oid_data)
        return RedirectResponse("/printer-oids", status_code=303)
    
    except Exception as e:
        logger.error(f"Error creating printer OIDs: {str(e)}")
        return templates.TemplateResponse(
            "printer_oids/form.html",
            {
                "request": request,
                "printer_oids": None,
                "error": str(e)
            }
        )

@router.get("/printer-oids/{oid_id}/edit")
async def edit_printer_oids_form(request: Request, oid_id: int, db: Session = Depends(get_db)):
    printer_oids_service = PrinterOIDsService(db)
    oids = printer_oids_service.get_by_id(oid_id)
    if not oids:
        return RedirectResponse("/printer-oids", status_code=303)
    return templates.TemplateResponse(
        "printer_oids/form.html",
        {"request": request, "printer_oids": oids}
    )

@router.post("/printer-oids/{oid_id}/edit")
async def edit_printer_oids(request: Request, oid_id: int, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        printer_oids_service = PrinterOIDsService(db)
        
        oid_data = {
            "brand": form.get("brand"),
            "model_family": form.get("model_family"),
            "description": form.get("description"),
            "oid_total_pages": form.get("oid_total_pages"),
            "oid_black_toner_level": form.get("oid_black_toner_level"),
            # Agregar todos los campos OID necesarios
        }
        
        await printer_oids_service.update(oid_id, oid_data)
        return RedirectResponse("/printer-oids", status_code=303)
    except Exception as e:
        logger.error(f"Error updating printer OIDs: {str(e)}")
        return templates.TemplateResponse(
            "printer_oids/form.html",
            {"request": request, "printer_oids": {"id": oid_id, **oid_data}, "error": str(e)}
        )

@router.delete("/printer-oids/{oid_id}")
async def delete_printer_oids(oid_id: int, db: Session = Depends(get_db)):
    try:
        printer_oids_service = PrinterOIDsService(db)
        success = await printer_oids_service.delete(oid_id)
        if success:
            return {"success": True}
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "OIDs configuration not found"}
        )
    except Exception as e:
        logger.error(f"Error deleting printer OIDs: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
        
        
# Agregar este endpoint en web.py

@router.post("/monitor/printers/create")
async def create_printer(request: Request, db: Session = Depends(get_db)):
   """
   Endpoint para crear una nueva impresora desde la interfaz web.
   """
   try:
       form_data = await request.json()
       logger.info(f"Recibiendo solicitud de creación de impresora con datos: {form_data}")
       
       # Validar datos requeridos
       required_fields = ["name", "model", "ip_address", "client_id"]
       for field in required_fields:
           if not form_data.get(field):
               logger.error(f"Campo requerido faltante: {field}")
               raise ValueError(f"El campo {field} es requerido")

       # Verificar que el cliente exista
       client = db.query(Client).filter(Client.id == form_data.get("client_id")).first()
       if not client:
           logger.error(f"Cliente no encontrado con ID: {form_data.get('client_id')}")
           raise ValueError("Cliente no válido")

       printer_service = PrinterMonitorService(db)
       
       printer_data = {
           "name": form_data.get("name"),
           "brand": form_data.get("brand")
           "model": form_data.get("model"),
           "ip_address": form_data.get("ip_address"),
           "client_id": form_data.get("client_id"),
           "status": "offline"
       }
       
       logger.debug(f"Datos de impresora a crear: {printer_data}")
       
       new_printer = printer_service.update_printer_data(
           agent_id=1,  # ID del agente por defecto
           printer_data=printer_data
       )
       
       logger.info(f"Impresora creada exitosamente con ID: {new_printer.id}")
       
       return JSONResponse(content={
           "status": "success",
           "printer_id": new_printer.id,
           "message": "Impresora creada exitosamente"
       })
       
   except ValueError as e:
       logger.error(f"Error de validación al crear impresora: {str(e)}")
       return JSONResponse(
           status_code=400,
           content={
               "status": "error",
               "detail": str(e)
           }
       )
   except Exception as e:
       logger.error(f"Error inesperado al crear impresora: {str(e)}")
       return JSONResponse(
           status_code=500,
           content={
               "status": "error",
               "detail": "Error interno al crear la impresora"
           }
       )
@router.delete("/monitor/printers/{printer_id}")
async def delete_printer(printer_id: int, db: Session = Depends(get_db)):
    try:
        printer = db.query(Printer).filter(Printer.id == printer_id).first()
        if not printer:
            return JSONResponse(
                status_code=404,
                content={"success": False, "detail": "Impresora no encontrada"}
            )
        
        db.delete(printer)
        db.commit()
        
        logger.info(f"Impresora {printer_id} eliminada exitosamente")
        return JSONResponse(content={"success": True})
        
    except Exception as e:
        logger.error(f"Error eliminando impresora {printer_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )