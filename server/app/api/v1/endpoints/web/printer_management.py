from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import RedirectResponse, JSONResponse
from app.db.session import get_db
from app.services.printer_monitor_service import PrinterMonitorService
from app.services.client_service import ClientService
from app.db.models.printer import Printer
from app.db.models.client import Client
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/monitor/printers")
async def list_printers(request: Request, db: Session = Depends(get_db)):
    """
    Lista todas las impresoras con sus estados y estadísticas
    """
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
    """
    Elimina una impresora existente
    """
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

@router.get("/printers/{printer_id}/alerts")
async def get_printer_alerts(printer_id: int, db: Session = Depends(get_db)):
    """
    Obtiene las alertas activas de una impresora
    """
    try:
        printer_service = PrinterMonitorService(db)
        alerts = await printer_service.get_printer_alerts(printer_id)
        return JSONResponse(content={"alerts": alerts})
    except Exception as e:
        logger.error(f"Error obteniendo alertas de impresora {printer_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.post("/printers/{printer_id}/alerts/acknowledge")
async def acknowledge_alert(printer_id: int, alert_id: int, db: Session = Depends(get_db)):
    """
    Marca una alerta como reconocida
    """
    try:
        printer_service = PrinterMonitorService(db)
        await printer_service.acknowledge_alert(printer_id, alert_id)
        return JSONResponse(content={"success": True})
    except Exception as e:
        logger.error(f"Error reconociendo alerta {alert_id} de impresora {printer_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )