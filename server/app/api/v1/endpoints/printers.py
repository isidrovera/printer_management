# server/app/api/v1/endpoints/printers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.driver_service import DriverService  # Actualizamos el import
from app.api.v1.endpoints.websocket import manager
from typing import List, Dict, Any
from app.db.models.printer import Printer
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class PrinterInstallRequest(BaseModel):
    printer_ip: str
    driver_id: int

router = APIRouter()

@router.post("/install/{agent_token}")
async def install_printer(
    agent_token: str,
    install_data: PrinterInstallRequest,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Iniciando instalación de impresora para agente {agent_token}")
        logger.debug(f"Datos recibidos: {install_data}")
        
        driver_service = DriverService(db)
        
        try:
            # Obtener información del driver con URL de descarga
            driver_info = await driver_service.get_driver_for_installation(install_data.driver_id)
            logger.debug(f"Información del driver obtenida: {driver_info}")
            
            # Preparar comando de instalación
            installation_command = {
                "type": "install_printer",  # Asegurarse de incluir el tipo
                "printer_ip": install_data.printer_ip,
                "manufacturer": driver_info["manufacturer"],
                "model": driver_info["model"],
                "driver_url": driver_info["download_url"],
                "driver_filename": driver_info["driver_filename"]
            }
            
            # Enviar comando al agente
            await manager.send_install_printer_command(agent_token, installation_command)
            logger.info("Comando de instalación enviado exitosamente")
            
            return {
                "status": "success",
                "message": "Comando de instalación enviado correctamente",
                "details": {
                    "printer_ip": install_data.printer_ip,
                    "driver": f"{driver_info['manufacturer']} {driver_info['model']}"
                }
            }
            
        except HTTPException as he:
            logger.error(f"Error HTTP durante la instalación: {he.detail}")
            raise he
        except Exception as e:
            logger.error(f"Error inesperado durante la instalación: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
            
    except Exception as e:
        logger.error(f"Error crítico en install_printer: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la instalación: {str(e)}"
        )

@router.get("/monitored", response_model=List[Dict[str, Any]])
async def get_monitored_printers(
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de impresoras configuradas para monitoreo.
    """
    try:
        query = db.query(Printer).filter(
            Printer.is_active == True
        ).with_entities(
            Printer.ip_address,
            Printer.brand,
            Printer.oid_config_id
        ).all()
        
        printers = []
        for printer in query:
            printer_data = {
                "ip_address": printer.ip_address,
                "brand": printer.brand,
                "oid_config_id": printer.oid_config_id
            }
            printers.append(printer_data)
            
        return printers
        
    except Exception as e:
        logger.error(f"Error getting monitored printers: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/monitored/{agent_id}", response_model=List[Dict[str, Any]])
async def get_agent_printers(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene las impresoras asignadas a un agente específico"""
    try:
        printers = db.query(Printer).filter(
            Printer.agent_id == agent_id,
            Printer.is_active == True
        ).all()
        
        result = []
        for printer in printers:
            printer_data = {
                "ip_address": printer.ip_address,
                "brand": printer.brand,
                "model": printer.model,
                "id": printer.id
            }
            result.append(printer_data)
            
        logger.info(f"Retornando {len(result)} impresoras para el agente {agent_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo impresoras del agente {agent_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))