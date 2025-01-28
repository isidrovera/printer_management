# server/app/api/v1/endpoints/printers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.printer_driver_service import PrinterDriverService
from app.api.v1.endpoints.websocket import manager
from typing import Dict
from pydantic import BaseModel

class PrinterInstallData(BaseModel):
    printer_ip: str
    driver_id: int

router = APIRouter()

@router.post("/install/{agent_token}")
async def install_printer(
    agent_token: str,
    printer_data: PrinterInstallData,
    db: Session = Depends(get_db)
):
    """
    Envía comando para instalar una impresora a un agente específico.
    """
    try:
        # Obtener el driver por ID
        driver_service = PrinterDriverService(db)
        driver = await driver_service.get_driver_by_id(printer_data.driver_id)
        
        if not driver:
            raise HTTPException(
                status_code=404,
                detail="Driver not found"
            )
        
        # Preparar datos del driver
        driver_data = await driver_service.get_driver_info(driver)
        
        # Preparar datos completos para el comando
        install_data = {
            "printer_ip": printer_data.printer_ip,
            "manufacturer": driver.manufacturer,
            "model": driver.model,
            "driver_data": driver_data
        }
        
        # Enviar comando al agente
        await manager.send_install_printer_command(agent_token, install_data)
        
        return {"status": "success", "message": "Install command sent successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )