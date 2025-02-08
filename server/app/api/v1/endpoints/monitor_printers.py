# server/app/api/v1/endpoints/monitor_printers.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.db.models.printer import Printer
from datetime import datetime

from app.db.session import get_db
from app.services.monitor_service import PrinterMonitorService
from app.core.logging import logger

router = APIRouter()

# server/app/api/v1/endpoints/monitor_printers.py

@router.post("/update", response_model=Dict[str, Any])
def update_printer_data(
    printer_data: Dict[str, Any],
    agent_id: int,
    db: Session = Depends(get_db)
) -> Printer:
    """
    Actualiza los datos de una impresora para un agente específico.
    """
    try:
        logger.info(f"Iniciando creación/actualización de impresora con datos: {printer_data}")
        
        monitor_service = PrinterMonitorService(db)
        printer = monitor_service.update_printer_data(
            printer_data=printer_data,
            agent_id=agent_id
        )
        
        return {
            "status": "success",
            "printer_id": printer.id,
            "message": "Impresora actualizada exitosamente"
        }
        
    except ValueError as ve:
        logger.error(f"Error de validación: {str(ve)}")
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as e:
        logger.error(f"Error inesperado en update_printer_data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/critical-supplies", response_model=List[Dict[str, Any]])
def get_critical_supplies(
    db: Session = Depends(get_db)
):
    """
    Obtiene impresoras con consumibles en estado crítico.
    """
    try:
        monitor_service = PrinterMonitorService(db)
        critical_printers = monitor_service.get_printers_with_critical_supplies()
        return [
            {
                "printer_id": printer.id,
                "printer_name": printer.name,
                "critical_supplies": printer.check_critical_supplies()
            } 
            for printer in critical_printers
        ]
    except Exception as e:
        logger.error(f"Error retrieving critical supplies: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/report", response_model=Dict[str, Any])
def generate_printer_report(
    db: Session = Depends(get_db)
):
    """
    Genera un informe general de impresoras.
    """
    try:
        monitor_service = PrinterMonitorService(db)
        report = monitor_service.generate_printer_report()
        return report
    except Exception as e:
        logger.error(f"Error generating printer report: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{printer_id}/history", response_model=Dict[str, List])
def get_printer_history(
    printer_id: int, 
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de una impresora específica.
    
    - Por defecto recupera el historial de los últimos 7 días
    """
    try:
        monitor_service = PrinterMonitorService(db)
        history = monitor_service.get_printer_history(printer_id, days)
        return history
    except Exception as e:
        logger.error(f"Error retrieving printer history for printer {printer_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
@router.post("/create", response_model=Dict[str, Any])
async def create_printer(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint para crear una nueva impresora.
    """
    try:
        # Obtener los datos del formulario
        form_data = await request.json()
        logger.info(f"Recibiendo solicitud de creación de impresora con datos: {form_data}")
        
        monitor_service = PrinterMonitorService(db)
        
        # Crear el diccionario con todos los campos necesarios
        printer_data = {}
        
        # Copiar todos los campos necesarios del form_data
        for field in ["name", "brand", "model", "ip_address", "client_id"]:
            if field in form_data:
                printer_data[field] = form_data[field]
                
        # Agregar el estado por defecto
        printer_data["status"] = "offline"
        
        logger.debug(f"Datos de impresora a crear: {printer_data}")
        
        try:
            new_printer = monitor_service.update_printer_data(
                agent_id=form_data.get("agent_id", 1),
                printer_data=printer_data
            )
            
            return {
                "status": "success",
                "printer_id": new_printer.id,
                "message": "Impresora creada exitosamente"
            }
            
        except ValueError as ve:
            logger.error(f"Error de validación al crear impresora: {str(ve)}")
            raise HTTPException(status_code=400, detail=str(ve))
            
    except HTTPException as he:
        raise he
        
    except Exception as e:
        logger.error(f"Error inesperado al crear impresora: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/monitor/printers/{printer_id}")
async def delete_printer(printer_id: int, db: Session = Depends(get_db)):
    try:
        printer = db.query(Printer).filter(Printer.id == printer_id).first()
        if not printer:
            raise HTTPException(status_code=404, detail="Impresora no encontrada")
        
        db.delete(printer)
        db.commit()
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Error eliminando impresora: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/", response_model=List[Dict[str, Any]])
def get_printers(
    db: Session = Depends(get_db),
    agent_id: Optional[int] = None
):
    """
    Obtiene todas las impresoras o las filtradas por agente.
    """
    try:
        logger.info(f"Obteniendo impresoras" + (f" para agente {agent_id}" if agent_id else ""))
        
        monitor_service = PrinterMonitorService(db)
        query = db.query(Printer)
        
        if agent_id:
            query = query.filter(Printer.agent_id == agent_id)
            
        printers = query.all()
        
        return [
            {
                "ip_address": printer.ip_address,
                "brand": printer.brand or "",  # Asegurarse de que no sea None
                "model": printer.model,
                "name": printer.name,
                "status": printer.status,
                "client_id": printer.client_id
            }
            for printer in printers
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo impresoras: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/printers/{printer_id}/counters", response_model=Dict[str, Any])
def get_printer_counters(
    printer_id: int, 
    db: Session = Depends(get_db)
):
    """
    Obtiene los contadores de una impresora específica.
    """
    logger.info(f"Solicitando contadores para impresora ID: {printer_id}")
    
    try:
        # Obtener la impresora
        printer = db.query(Printer).filter(Printer.id == printer_id).first()
        
        if not printer:
            logger.error(f"Impresora con ID {printer_id} no encontrada")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Impresora con ID {printer_id} no encontrada"
            )
        
        # Registro detallado de los datos de la impresora
        logger.info(f"Contenido completo de printer_data: {printer.printer_data}")
        
        # Obtener contadores
        counters = printer.printer_data.get('counters', {})
        logger.info(f"Contadores recuperados: {counters}")
        
        result = {
            "printer_id": printer.id,
            "name": printer.name,
            "current": {
                "total": counters.get('total_pages', 0),
                "color": counters.get('color_pages', 0),
                "bw": counters.get('bw_pages', 0)
            },
            "history": {}
        }
        
        logger.info(f"Resultado final de contadores: {result}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error completo al obtener contadores: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener contadores: {str(e)}"
        )


@router.get("/printers/{printer_id}/supplies", response_model=Dict[str, Any])
def get_printer_supplies(
    printer_id: int, 
    db: Session = Depends(get_db)
):
    """
    Obtiene los niveles de suministros de una impresora específica.
    """
    printer = db.query(Printer).filter(Printer.id == printer_id).first()
    
    if not printer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Impresora con ID {printer_id} no encontrada"
        )
    
    # Extraer suministros del printer_data
    printer_data = printer.printer_data or {}
    supplies = printer_data.get('supplies', {})
    
    return {
        "printer_id": printer.id,
        "name": printer.name,
        "supplies": {
            "toners": {
                "black": supplies.get('toners', {}).get('black', {}).get('percentage', 0),
                "cyan": supplies.get('toners', {}).get('cyan', {}).get('percentage', 0),
                "magenta": supplies.get('toners', {}).get('magenta', {}).get('percentage', 0),
                "yellow": supplies.get('toners', {}).get('yellow', {}).get('percentage', 0)
            },
            "drums": {
                "black": supplies.get('drums', {}).get('black', {}).get('percentage', 0),
                "cyan": supplies.get('drums', {}).get('cyan', {}).get('percentage', 0),
                "magenta": supplies.get('drums', {}).get('magenta', {}).get('percentage', 0),
                "yellow": supplies.get('drums', {}).get('yellow', {}).get('percentage', 0)
            }
        }
    }