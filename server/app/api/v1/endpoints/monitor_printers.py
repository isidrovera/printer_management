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
    printer_data: Dict[str, Any], 
    db: Session = Depends(get_db)
):
    """
    Endpoint para actualizar datos de una impresora.
    
    Permite a los agentes enviar información actualizada de una impresora.
    """
    try:
        monitor_service = PrinterMonitorService(db)
        updated_printer = monitor_service.update_printer_data(printer_data)
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