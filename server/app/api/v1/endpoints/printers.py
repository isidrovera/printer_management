# server/app/api/v1/endpoints/printers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.printer_driver_service import PrinterDriverService
from app.api.v1.endpoints.websocket import manager
from typing import Dict

router = APIRouter()

@router.post("/install/{agent_token}")
async def install_printer(
    agent_token: str,
    printer_data: Dict,
    db: Session = Depends(get_db)
):
    """
    Envía comando para instalar una impresora a un agente específico.
    
    printer_data debe contener:
    - printer_ip: str
    - manufacturer: str
    - model: str
    """
    try:
        # Obtener el driver correspondiente
        driver_service = PrinterDriverService(db)
        driver = await driver_service.get_driver(
            printer_data["manufacturer"],
            printer_data["model"]
        )
        
        if not driver:
            raise HTTPException(
                status_code=404,
                detail="Printer driver not found"
            )
        
        # Preparar datos del driver
        driver_data = await driver_service.get_driver_info(driver)
        
        # Agregar datos del driver a la información de la impresora
        printer_data["driver_data"] = driver_data
        
        # Enviar comando al agente
        await manager.send_install_printer_command(agent_token, printer_data)
        
        return {"status": "success", "message": "Install command sent successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )