# server/app/api/v1/endpoints/printers.py
from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.printer_service import PrinterService
from app.schemas.printer import PrinterCreate, Printer, PrinterUpdate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def list_printers(request: Request, db: Session = Depends(get_db)):
    """Lista todas las impresoras"""
    try:
        logger.info("Obteniendo lista de impresoras")
        printer_service = PrinterService(db)
        printers = await printer_service.get_printers(skip=0, limit=100)
        oid_configs = await printer_service.get_oid_configs()
        
        logger.info(f"Se encontraron {len(printers)} impresoras")
        return templates.TemplateResponse(
            "printers/list.html",
            {
                "request": request,
                "printers": printers,
                "oid_configs": oid_configs
            }
        )
    except Exception as e:
        logger.error(f"Error listando impresoras: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Printer, status_code=status.HTTP_201_CREATED)
async def create_printer(data: PrinterCreate, db: Session = Depends(get_db)):
    """Crea una nueva impresora"""
    try:
        logger.info(f"Creando nueva impresora: {data.name}")
        printer_service = PrinterService(db)
        printer = await printer_service.create_printer(data)
        logger.info(f"Impresora creada con ID: {printer.id}")
        return printer
    except Exception as e:
        logger.error(f"Error creando impresora: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{printer_id}", response_model=Printer)
async def get_printer(printer_id: int, db: Session = Depends(get_db)):
    """Obtiene detalles de una impresora"""
    try:
        logger.info(f"Obteniendo información de impresora {printer_id}")
        printer_service = PrinterService(db)
        printer = await printer_service.get_printer(printer_id)
        if not printer:
            logger.warning(f"Impresora {printer_id} no encontrada")
            raise HTTPException(status_code=404, detail="Printer not found")
        return printer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo impresora: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{printer_id}", response_model=Printer)
async def update_printer(printer_id: int, data: PrinterUpdate, db: Session = Depends(get_db)):
    """Actualiza una impresora existente"""
    try:
        logger.info(f"Actualizando impresora {printer_id}")
        printer_service = PrinterService(db)
        printer = await printer_service.update_printer(printer_id, data)
        if not printer:
            logger.warning(f"Impresora {printer_id} no encontrada")
            raise HTTPException(status_code=404, detail="Printer not found")
        logger.info(f"Impresora {printer_id} actualizada exitosamente")
        return printer
    except Exception as e:
        logger.error(f"Error actualizando impresora: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_printer(printer_id: int, db: Session = Depends(get_db)):
    """Elimina una impresora"""
    try:
        logger.info(f"Eliminando impresora {printer_id}")
        printer_service = PrinterService(db)
        if not await printer_service.delete_printer(printer_id):
            logger.warning(f"Impresora {printer_id} no encontrada")
            raise HTTPException(status_code=404, detail="Printer not found")
        logger.info(f"Impresora {printer_id} eliminada exitosamente")
    except Exception as e:
        logger.error(f"Error eliminando impresora: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{printer_id}/scan", status_code=status.HTTP_200_OK)
async def scan_printer(printer_id: int, db: Session = Depends(get_db)):
    """Escanea una impresora vía SNMP"""
    try:
        logger.info(f"Iniciando escaneo SNMP de impresora {printer_id}")
        printer_service = PrinterService(db)
        result = await printer_service.scan_printer(printer_id)
        logger.info(f"Escaneo de impresora {printer_id} completado")
        return result
    except Exception as e:
        logger.error(f"Error escaneando impresora: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{printer_id}/history", status_code=status.HTTP_200_OK)
async def get_printer_history(printer_id: int, db: Session = Depends(get_db)):
    """Obtiene historial de una impresora"""
    try:
        logger.info(f"Obteniendo historial de impresora {printer_id}")
        printer_service = PrinterService(db)
        history = await printer_service.get_printer_history(printer_id)
        return history
    except Exception as e:
        logger.error(f"Error obteniendo historial: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))