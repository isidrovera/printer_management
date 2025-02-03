# server/app/api/v1/endpoints/monitor_printers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.api.deps import get_db
from app.services.monitor_service import PrinterMonitorService
from app.core.security import get_current_agent, get_current_user
from app.schemas.printer import PrinterUpdate  # Asumo que tienes un esquema de validación

router = APIRouter()

@router.post("/update", response_model=Dict[str, Any])
def update_printer_data(
    printer_data: PrinterUpdate, 
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent)
):
    """
    Endpoint para que los agentes actualicen los datos de una impresora.
    
    - Solo los agentes autenticados pueden actualizar datos de impresoras
    - El agente debe tener permisos para actualizar impresoras de su cliente
    """
    try:
        monitor_service = PrinterMonitorService(db)
        updated_printer = monitor_service.update_printer_data(
            agent_id=current_agent.id, 
            printer_data=printer_data.dict()
        )
        return {
            "status": "success",
            "printer_id": updated_printer.id,
            "message": "Printer data updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/agent/printers", response_model=List[Dict[str, Any]])
def get_printers_by_agent(
    db: Session = Depends(get_db),
    current_agent = Depends(get_current_agent)
):
    """
    Obtiene todas las impresoras asociadas al agente actual.
    """
    try:
        monitor_service = PrinterMonitorService(db)
        printers = monitor_service.get_printers_by_agent(current_agent.id)
        return [printer.to_dict() for printer in printers]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/critical-supplies", response_model=List[Dict[str, Any]])
def get_critical_supplies(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # Puede ser accedido por usuarios autorizados
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
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/report", response_model=Dict[str, Any])
def generate_printer_report(
    agent_id: int = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Genera un informe general de impresoras.
    
    - Si se proporciona agent_id, filtra el informe para ese agente
    - Requiere autenticación de usuario
    """
    try:
        monitor_service = PrinterMonitorService(db)
        report = monitor_service.generate_printer_report(agent_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{printer_id}/history", response_model=Dict[str, List])
def get_printer_history(
    printer_id: int, 
    days: int = 7,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obtiene el historial de una impresora específica.
    
    - Por defecto recupera el historial de los últimos 7 días
    - Requiere autenticación de usuario
    """
    try:
        monitor_service = PrinterMonitorService(db)
        history = monitor_service.get_printer_history(printer_id, days)
        return history
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))