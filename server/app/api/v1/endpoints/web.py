# server/app/api/v1/endpoints/web.py
from fastapi import APIRouter, Request, Depends
from typing import Optional
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
from app.db.models.client import Client, ClientStatus, ClientType
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
        # Inicializar servicio de impresoras
        try:
            printer_service = PrinterMonitorService(db)
            has_printer_service = True
            logger.debug("Servicio de impresoras inicializado correctamente")
        except Exception as e:
            has_printer_service = False
            logger.warning(f"Error al inicializar el servicio de impresoras: {str(e)}")
        # Obtener estadísticas de clientes
        logger.debug("Obteniendo estadísticas de clientes")
        total_clients = await client_service.get_count()
        logger.info(f"Total de clientes obtenidos: {total_clients}")
        # Obtener estadísticas de clientes
        logger.debug("Obteniendo estadísticas de clientes")
        client_stats = await client_service.get_dashboard_stats()
        logger.info(f"Total de clientes obtenidos: {client_stats['total']}")


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
            "clients": client_stats,
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
# Rutas para el manejo de clientes
@router.get("/clients")
async def list_clients(
    request: Request, 
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Vista de listado de clientes con opciones de filtrado"""
    try:
        client_service = ClientService(db)
        if search:
            clients = await client_service.search_clients(search)
        elif status:
            clients = await client_service.get_by_status(ClientStatus(status))
        else:
            clients = await client_service.get_all()
            
        return templates.TemplateResponse(
            "clients/list.html",
            {
                "request": request, 
                "clients": clients,
                "statuses": ClientStatus,
                "current_search": search,
                "current_status": status
            }
        )
    except Exception as e:
        logger.error(f"Error listing clients: {str(e)}")
        return templates.TemplateResponse(
            "clients/list.html",
            {"request": request, "clients": [], "error": str(e)}
        )

@router.get("/clients/create")
async def create_client_form(request: Request):
    """Formulario de creación de cliente"""
    return templates.TemplateResponse(
        "clients/form.html",
        {
            "request": request,
            "client": None,
            "client_types": ClientType,
            "client_statuses": ClientStatus
        }
    )

@router.post("/clients/create")
async def create_client(request: Request, db: Session = Depends(get_db)):
    """Procesa la creación de un nuevo cliente"""
    try:
        form = await request.form()
        client_data = {
            "name": form.get("name"),
            "business_name": form.get("business_name"),
            "tax_id": form.get("tax_id"),
            "client_type": form.get("client_type"),
            "contact_name": form.get("contact_name"),
            "contact_email": form.get("contact_email"),
            "contact_phone": form.get("contact_phone"),
            "contact_position": form.get("contact_position"),
            "technical_contact_name": form.get("technical_contact_name"),
            "technical_contact_email": form.get("technical_contact_email"),
            "technical_contact_phone": form.get("technical_contact_phone"),
            "billing_contact_name": form.get("billing_contact_name"),
            "billing_contact_email": form.get("billing_contact_email"),
            "billing_contact_phone": form.get("billing_contact_phone"),
            "billing_address": form.get("billing_address"),
            "billing_city": form.get("billing_city"),
            "billing_state": form.get("billing_state"),
            "billing_zip_code": form.get("billing_zip_code"),
            "billing_country": form.get("billing_country"),
            "service_address": form.get("service_address"),
            "service_city": form.get("service_city"),
            "service_state": form.get("service_state"),
            "service_zip_code": form.get("service_zip_code"),
            "service_country": form.get("service_country"),
            "contract_number": form.get("contract_number"),
            "contract_start_date": form.get("contract_start_date"),
            "contract_end_date": form.get("contract_end_date"),
            "payment_terms": form.get("payment_terms"),
            "credit_limit": form.get("credit_limit"),
            "account_manager": form.get("account_manager"),
            "service_level": form.get("service_level"),
            "support_priority": form.get("support_priority"),
            "status": form.get("status"),
            "notes": form.get("notes")
        }

        client_service = ClientService(db)
        client = await client_service.create(client_data)
        
        logger.info(f"Cliente creado exitosamente: {client.name}")
        return RedirectResponse("/clients", status_code=303)
    
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        return templates.TemplateResponse(
            "clients/form.html",
            {
                "request": request,
                "client": None,
                "error": str(e),
                "client_types": ClientType,
                "client_statuses": ClientStatus,
                "form_data": client_data
            }
        )

@router.get("/clients/{client_id}/edit")
async def edit_client_form(request: Request, client_id: int, db: Session = Depends(get_db)):
    """Formulario de edición de cliente"""
    client_service = ClientService(db)
    client = await client_service.get_by_id(client_id)
    
    if not client:
        return RedirectResponse("/clients", status_code=303)
        
    return templates.TemplateResponse(
        "clients/form.html",
        {
            "request": request,
            "client": client,
            "client_types": ClientType,
            "client_statuses": ClientStatus
        }
    )

@router.post("/clients/{client_id}/edit")
async def edit_client(request: Request, client_id: int, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        
        def clean_value(value):
            if value in ['None', 'none', '', None]:
                return None
            return value

        def parse_date(date_str):
            if not date_str or date_str in ['None', 'none', '']:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return None

        def get_enum_value(enum_class, value):
            if not value:
                return None
            try:
                # Convertir el valor a mayúsculas para coincidir con el enum
                return enum_class[value.upper()]
            except KeyError:
                return None

        # Mapeo de prioridades a valores enteros
        PRIORITY_MAP = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }

        # Convertir credit_limit a Integer
        try:
            credit_limit = int(float(form.get('credit_limit', 0))) if form.get('credit_limit') else None
        except ValueError:
            credit_limit = None

        # Obtener los valores de enum de forma segura
        client_type = get_enum_value(ClientType, form.get("client_type"))
        status = get_enum_value(ClientStatus, form.get("status"))

        client_data = {
            # Información Básica
            "name": clean_value(form.get("name")),
            "business_name": clean_value(form.get("business_name")),
            "tax_id": clean_value(form.get("tax_id")),
            "client_type": client_type,  # Usando el enum directamente
            "status": status,  # Usando el enum directamente
            "client_code": clean_value(form.get("client_code")),

            # Contacto de Facturación
            "billing_contact_name": clean_value(form.get("billing_contact_name")),
            "billing_contact_email": clean_value(form.get("billing_contact_email")),
            "billing_contact_phone": clean_value(form.get("billing_contact_phone")),

            # Dirección de Facturación
            "billing_address": clean_value(form.get("billing_address")),
            "billing_city": clean_value(form.get("billing_city")),
            "billing_state": clean_value(form.get("billing_state")),
            "billing_zip_code": clean_value(form.get("billing_zip_code")),
            "billing_country": clean_value(form.get("billing_country")),

            # Información del Contrato
            "contract_number": clean_value(form.get("contract_number")),
            "contract_start_date": parse_date(form.get("contract_start_date")),
            "contract_end_date": parse_date(form.get("contract_end_date")),
            "service_level": clean_value(form.get("service_level")),
            "payment_terms": clean_value(form.get("payment_terms")),
            "credit_limit": credit_limit,

            # Información Adicional
            "account_manager": clean_value(form.get("account_manager")),
            "support_priority": PRIORITY_MAP.get(form.get('support_priority', '').lower(), 1),
            "notes": clean_value(form.get("notes")),

            # Campos de control
            "updated_at": datetime.utcnow()
        }

        # Eliminar valores None y valores de enum no válidos
        client_data = {k: v for k, v in client_data.items() if v is not None}

        logger.debug(f"Datos a actualizar para cliente {client_id}: {client_data}")
        
        client_service = ClientService(db)
        client = await client_service.update(client_id, client_data)
        
        if not client:
            raise ValueError("Cliente no encontrado")

        logger.info(f"Cliente {client_id} actualizado exitosamente")
        return RedirectResponse("/clients", status_code=303)
        
    except ValueError as e:
        logger.error(f"Error de validación al actualizar cliente: {str(e)}")
        return templates.TemplateResponse(
            "clients/form.html",
            {
                "request": request,
                "client": {
                    "id": client_id,
                    **form,
                    "contract_start_date": parse_date(form.get("contract_start_date")),
                    "contract_end_date": parse_date(form.get("contract_end_date"))
                },
                "error": str(e),
                "client_types": ClientType,
                "client_statuses": ClientStatus
            }
        )
    except Exception as e:
        logger.error(f"Error al actualizar cliente: {str(e)}")
        return templates.TemplateResponse(
            "clients/form.html",
            {
                "request": request,
                "client": {
                    "id": client_id,
                    **form,
                    "contract_start_date": parse_date(form.get("contract_start_date")),
                    "contract_end_date": parse_date(form.get("contract_end_date"))
                },
                "error": "Error al actualizar el cliente. Por favor, intente nuevamente.",
                "client_types": ClientType,
                "client_statuses": ClientStatus
            }
        )
@router.delete("/clients/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Elimina un cliente"""
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

# Rutas adicionales útiles
@router.get("/clients/{client_id}/details")
async def client_details(
    request: Request, 
    client_id: int, 
    db: Session = Depends(get_db)
):
    """Vista detallada de un cliente"""
    client_service = ClientService(db)
    client = await client_service.get_by_id(client_id)
    
    if not client:
        return RedirectResponse("/clients", status_code=303)
        
    # Verificar si la petición espera JSON (es una petición AJAX)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JSONResponse({
            "id": client.id,
            "name": client.name,
            "business_name": client.business_name,
            "tax_id": client.tax_id,
            "client_type": client.client_type.value if hasattr(client.client_type, 'value') else client.client_type,
            "status": client.status.value if hasattr(client.status, 'value') else client.status,
            "client_code": client.client_code,
            
            # Contactos
            "contact_info": {
                "name": client.contact_name,
                "email": client.contact_email,
                "phone": client.contact_phone
            },
            "technical_contact_info": {
                "name": client.technical_contact_name,
                "email": client.technical_contact_email,
                "phone": client.technical_contact_phone
            },
            "billing_contact_info": {
                "name": client.billing_contact_name,
                "email": client.billing_contact_email,
                "phone": client.billing_contact_phone
            },

            # Dirección
            "service_address": client.billing_address,
            "service_city": client.billing_city,
            "service_state": client.billing_state,
            "service_zip_code": client.billing_zip_code,
            "service_country": client.billing_country,

            # Contrato
            "contract_info": {
                "number": client.contract_number,
                "start_date": client.contract_start_date.strftime('%d/%m/%Y') if client.contract_start_date else None,
                "end_date": client.contract_end_date.strftime('%d/%m/%Y') if client.contract_end_date else None,
                "service_level": client.service_level,
                "payment_terms": client.payment_terms,
                "credit_limit": float(client.credit_limit) if client.credit_limit else 0.0
            }
        })
        
    # Si no es AJAX, devolver la vista HTML
    return templates.TemplateResponse(
        "clients/details.html",
        {"request": request, "client": client}
    )






#Manejo de agentes
#server/app/api/v1/endpoints/web.py
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
 
        
@router.get("/brands/{brand}")
def get_oids_by_brand(
    brand: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Obtiene las configuraciones de OIDs para una marca específica.
    """
    service = PrinterOIDsService(db)
    oids = (service.db.query(PrinterOIDs)
            .filter(PrinterOIDs.brand == brand)
            .offset(skip)
            .limit(limit)
            .all())
    
    if not oids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron configuraciones para la marca {brand}"
        )
    
    return oids
    
    
# ============= Manejo de OIDS de Impresoras =============

# 1. Listado de OIDs
@router.get("/printer-oids", name="list_printer_oids")
async def list_printer_oids(request: Request, db: Session = Depends(get_db)):
    """
    Muestra la lista de todas las configuraciones de OIDs
    """
    try:
        printer_oids_service = PrinterOIDsService(db)
        oids = printer_oids_service.get_all()
        return templates.TemplateResponse(
            "printer_oids/list.html",
            {"request": request, "printer_oids": oids}
        )
    except Exception as e:
        logger.error(f"Error al listar OIDs: {str(e)}")
        return templates.TemplateResponse(
            "printer_oids/list.html",
            {"request": request, "printer_oids": [], "error": str(e)}
        )

# 2. Creación de OIDs
@router.get("/printer-oids/create", name="create_printer_oids_form")
async def create_printer_oids_form(request: Request):
    """
    Muestra el formulario para crear nuevas configuraciones de OIDs
    """
    return templates.TemplateResponse(
        "printer_oids/form.html",
        {"request": request, "printer_oids": None}
    )

@router.post("/printer-oids/create", name="create_printer_oids")
async def create_printer_oids(request: Request, db: Session = Depends(get_db)):
    """
    Procesa la creación de nuevas configuraciones de OIDs
    """
    try:
        form = await request.form()
        
        # Recopilar todos los campos del formulario
        oid_data = {
            # Información básica
            "brand": form.get("brand"),
            "model_family": form.get("model_family"),
            "description": form.get("description"),
            
            # Contadores de páginas
            "oid_total_pages": form.get("oid_total_pages"),
            "oid_total_color_pages": form.get("oid_total_color_pages"),
            "oid_total_bw_pages": form.get("oid_total_bw_pages"),
            "oid_total_copies": form.get("oid_total_copies"),
            "oid_total_prints": form.get("oid_total_prints"),
            "oid_total_scans": form.get("oid_total_scans"),
            "oid_duplex_pages": form.get("oid_duplex_pages"),
            "oid_total_faxes": form.get("oid_total_faxes"),
            
            # Niveles de tóner
            "oid_black_toner_level": form.get("oid_black_toner_level"),
            "oid_cyan_toner_level": form.get("oid_cyan_toner_level"),
            "oid_magenta_toner_level": form.get("oid_magenta_toner_level"),
            "oid_yellow_toner_level": form.get("oid_yellow_toner_level"),
            
            # Capacidades máximas de tóner
            "oid_black_toner_max": form.get("oid_black_toner_max"),
            "oid_cyan_toner_max": form.get("oid_cyan_toner_max"),
            "oid_magenta_toner_max": form.get("oid_magenta_toner_max"),
            "oid_yellow_toner_max": form.get("oid_yellow_toner_max"),
            
            # Estados de tóner
            "oid_black_toner_status": form.get("oid_black_toner_status"),
            "oid_cyan_toner_status": form.get("oid_cyan_toner_status"),
            "oid_magenta_toner_status": form.get("oid_magenta_toner_status"),
            "oid_yellow_toner_status": form.get("oid_yellow_toner_status"),
            
            # Unidades de imagen/drums
            "oid_black_drum_level": form.get("oid_black_drum_level"),
            "oid_cyan_drum_level": form.get("oid_cyan_drum_level"),
            "oid_magenta_drum_level": form.get("oid_magenta_drum_level"),
            "oid_yellow_drum_level": form.get("oid_yellow_drum_level"),
            
            # Otros consumibles
            "oid_fuser_unit_level": form.get("oid_fuser_unit_level"),
            "oid_transfer_belt_level": form.get("oid_transfer_belt_level"),
            "oid_waste_toner_level": form.get("oid_waste_toner_level"),
            "oid_waste_toner_max": form.get("oid_waste_toner_max")
        }
        
        printer_oids_service = PrinterOIDsService(db)
        
        # Verificar existencia previa
        existing = printer_oids_service.get_by_brand_and_family(
            oid_data["brand"],
            oid_data["model_family"]
        )
        
        if existing:
            raise ValueError("Ya existe una configuración para esta marca y familia de modelos")
        
        # Crear nueva configuración
        await printer_oids_service.create(oid_data)
        return RedirectResponse("/printer-oids", status_code=303)
    
    except ValueError as e:
        logger.warning(f"Error de validación al crear OIDs: {str(e)}")
        return templates.TemplateResponse(
            "printer_oids/form.html",
            {
                "request": request,
                "printer_oids": None,
                "error": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error inesperado al crear OIDs: {str(e)}")
        return templates.TemplateResponse(
            "printer_oids/form.html",
            {
                "request": request,
                "printer_oids": None,
                "error": "Error interno al crear la configuración"
            }
        )

# 3. Edición de OIDs
@router.get("/printer-oids/{oid_id}/edit", name="edit_printer_oids_form")
async def edit_printer_oids_form(request: Request, oid_id: int, db: Session = Depends(get_db)):
    """
    Muestra el formulario para editar una configuración existente
    """
    printer_oids_service = PrinterOIDsService(db)
    oids = printer_oids_service.get_by_id(oid_id)
    if not oids:
        return RedirectResponse("/printer-oids", status_code=303)
    return templates.TemplateResponse(
        "printer_oids/form.html",
        {"request": request, "printer_oids": oids}
    )

@router.post("/printer-oids/{oid_id}/edit", name="edit_printer_oids")
async def edit_printer_oids(request: Request, oid_id: int, db: Session = Depends(get_db)):
    """
    Procesa la actualización de una configuración existente
    """
    try:
        form = await request.form()
        printer_oids_service = PrinterOIDsService(db)
        
        # Recopilar todos los campos actualizados
        oid_data = {
            "brand": form.get("brand"),
            "model_family": form.get("model_family"),
            "description": form.get("description"),
            # ... [incluir todos los campos como en create]
        }
        
        await printer_oids_service.update(oid_id, oid_data)
        return RedirectResponse("/printer-oids", status_code=303)
    except Exception as e:
        logger.error(f"Error al actualizar OIDs: {str(e)}")
        return templates.TemplateResponse(
            "printer_oids/form.html",
            {"request": request, "printer_oids": {"id": oid_id, **oid_data}, "error": str(e)}
        )

# 4. Eliminación de OIDs
@router.delete("/printer-oids/{oid_id}", name="delete_printer_oids")
async def delete_printer_oids(oid_id: int, db: Session = Depends(get_db)):
    """
    Elimina una configuración de OIDs existente
    """
    try:
        printer_oids_service = PrinterOIDsService(db)
        success = await printer_oids_service.delete(oid_id)
        if success:
            return {"success": True}
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Configuración de OIDs no encontrada"}
        )
    except Exception as e:
        logger.error(f"Error al eliminar OIDs: {str(e)}")
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
           "brand": form_data.get("brand"),
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


# Agregar estas rutas en web.py después de las rutas existentes

# ============= Manejo de Usuarios =============
@router.get("/users")
async def list_users(
    request: Request,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Vista de listado de usuarios con opciones de filtrado"""
    try:
        user_service = UserService(db)
        users = await user_service.get_all_users()
        
        return templates.TemplateResponse(
            "users/list.html",
            {
                "request": request,
                "users": users,
                "roles": UserRole,
                "statuses": UserStatus,
                "departments": UserDepartment,
                "current_search": search,
                "current_role": role,
                "current_status": status
            }
        )
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        return templates.TemplateResponse(
            "users/list.html",
            {
                "request": request,
                "users": [],
                "roles": UserRole,
                "statuses": UserStatus,
                "departments": UserDepartment,
                "error": str(e)
            }
        )

@router.get("/users/create")
async def create_user_form(request: Request):
    """Formulario de creación de usuario"""
    return templates.TemplateResponse(
        "users/form.html",
        {
            "request": request,
            "user": None,
            "roles": UserRole,
            "statuses": UserStatus,
            "departments": UserDepartment
        }
    )

@router.post("/users/create")
async def create_user(request: Request, db: Session = Depends(get_db)):
    """Procesa la creación de un nuevo usuario"""
    try:
        form = await request.form()
        user_data = UserCreate(
            username=form.get("username"),
            email=form.get("email"),
            password=form.get("password"),
            full_name=form.get("full_name"),
            role=form.get("role", UserRole.VIEWER),
            department=form.get("department")
        )

        user_service = UserService(db)
        user = await user_service.create_user(user_data)
        
        logger.info(f"Usuario creado exitosamente: {user.username}")
        return RedirectResponse("/users", status_code=303)
    
    except HTTPException as e:
        logger.warning(f"Error de validación al crear usuario: {str(e)}")
        return templates.TemplateResponse(
            "users/form.html",
            {
                "request": request,
                "user": None,
                "error": e.detail,
                "roles": UserRole,
                "statuses": UserStatus,
                "departments": UserDepartment,
                "form_data": dict(form)
            }
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return templates.TemplateResponse(
            "users/form.html",
            {
                "request": request,
                "user": None,
                "error": str(e),
                "roles": UserRole,
                "statuses": UserStatus,
                "departments": UserDepartment,
                "form_data": dict(form)
            }
        )

@router.get("/users/{user_id}/edit")
async def edit_user_form(request: Request, user_id: int, db: Session = Depends(get_db)):
    """Formulario de edición de usuario"""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        return RedirectResponse("/users", status_code=303)
        
    return templates.TemplateResponse(
        "users/form.html",
        {
            "request": request,
            "user": user,
            "roles": UserRole,
            "statuses": UserStatus,
            "departments": UserDepartment
        }
    )

@router.post("/users/{user_id}/edit")
async def edit_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    """Procesa la edición de un usuario"""
    try:
        form = await request.form()
        
        def clean_value(value):
            return None if value in ['None', 'none', '', None] else value

        user_data = UserUpdate(
            email=clean_value(form.get("email")),
            full_name=clean_value(form.get("full_name")),
            job_title=clean_value(form.get("job_title")),
            department=clean_value(form.get("department")),
            phone=clean_value(form.get("phone")),
            mobile=clean_value(form.get("mobile")),
            role=clean_value(form.get("role")),
            status=clean_value(form.get("status"))
        )

        user_service = UserService(db)
        user = await user_service.update_user(user_id, user_data)
        
        if not user:
            raise ValueError("Usuario no encontrado")

        logger.info(f"Usuario {user_id} actualizado exitosamente")
        return RedirectResponse("/users", status_code=303)
        
    except ValueError as e:
        logger.warning(f"Error de validación al actualizar usuario: {str(e)}")
        return templates.TemplateResponse(
            "users/form.html",
            {
                "request": request,
                "user": {"id": user_id, **dict(form)},
                "error": str(e),
                "roles": UserRole,
                "statuses": UserStatus,
                "departments": UserDepartment
            }
        )
    except Exception as e:
        logger.error(f"Error al actualizar usuario: {str(e)}")
        return templates.TemplateResponse(
            "users/form.html",
            {
                "request": request,
                "user": {"id": user_id, **dict(form)},
                "error": "Error al actualizar el usuario. Por favor, intente nuevamente.",
                "roles": UserRole,
                "statuses": UserStatus,
                "departments": UserDepartment
            }
        )

@router.get("/users/{user_id}/change-password")
async def change_password_form(request: Request, user_id: int, db: Session = Depends(get_db)):
    """Formulario para cambio de contraseña"""
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        return RedirectResponse("/users", status_code=303)
        
    return templates.TemplateResponse(
        "users/change_password.html",
        {
            "request": request,
            "user": user
        }
    )

@router.post("/users/{user_id}/change-password")
async def change_password(request: Request, user_id: int, db: Session = Depends(get_db)):
    """Procesa el cambio de contraseña"""
    try:
        form = await request.form()
        current_password = form.get("current_password")
        new_password = form.get("new_password")
        confirm_password = form.get("confirm_password")
        
        if new_password != confirm_password:
            raise ValueError("Las contraseñas no coinciden")
            
        user_service = UserService(db)
        success = await user_service.change_password(user_id, current_password, new_password)
        
        if success:
            return RedirectResponse("/users", status_code=303)
        raise ValueError("Error al cambiar la contraseña")
        
    except Exception as e:
        logger.error(f"Error al cambiar contraseña: {str(e)}")
        return templates.TemplateResponse(
            "users/change_password.html",
            {
                "request": request,
                "user_id": user_id,
                "error": str(e)
            }
        )

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Desactiva un usuario (soft delete)"""
    try:
        user_service = UserService(db)
        success = await user_service.deactivate_user(user_id)
        
        if success:
            return {"success": True}
            
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Usuario no encontrado"}
        )
    except Exception as e:
        logger.error(f"Error desactivando usuario: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )