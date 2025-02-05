# server/app/api/v1/endpoints/monitor_printers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.db.session import get_db
from app.services.monitor_service import PrinterMonitorService
from app.core.logging import logger

router = APIRouter()

@router.post("/update", response_model=Dict[str, Any])
def update_printer_data(
    agent_id: int,  # Añadir como parámetro de consulta
    printer_data: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """
    Endpoint para actualizar datos de una impresora.
    
    Permite a los agentes enviar información actualizada de una impresora.
    """
    try:
        monitor_service = PrinterMonitorService(db)
        updated_printer = monitor_service.update_printer_data(agent_id, printer_data)
        return {
            "status": "success",
            "printer_id": updated_printer.id,
            "message": "Printer data updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating printer data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
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
        form_data = await request.json()
        monitor_service = PrinterMonitorService(db)
        
        printer_data = {
            "name": form_data.get("name"),
            "model": form_data.get("model"),
            "ip_address": form_data.get("ip_address"),
            "status": "offline",  # Estado inicial
            "supplies": {
                "black": {"level": 100},
                "cyan": {"level": 100},
                "magenta": {"level": 100},
                "yellow": {"level": 100}
            },
            "counters": {
                "total": 0,
                "color": 0,
                "bw": 0
            }
        }
        
        # Usar el método existente para crear/actualizar
        new_printer = monitor_service.update_printer_data(
            agent_id=form_data.get("agent_id", 1),  # ID del agente por defecto
            printer_data=printer_data
        )
        
        return JSONResponse(content={
            "status": "success",
            "printer_id": new_printer.id,
            "message": "Impresora creada exitosamente"
        })
        
    except Exception as e:
        logger.error(f"Error creating printer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))