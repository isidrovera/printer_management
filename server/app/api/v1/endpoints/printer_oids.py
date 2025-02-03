# server/app/api/v1/endpoints/printer_oids.py
from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.printer_oids_service import PrinterOIDsService
from app.schemas.printer_oids import PrinterOIDsCreate, PrinterOIDs, PrinterOIDsUpdate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def list_printer_oids(request: Request, db: Session = Depends(get_db)):
    """Lista todas las configuraciones de OIDs."""
    try:
        logger.info("Obteniendo lista de configuraciones OID")
        oids_service = PrinterOIDsService(db)
        oids_configs = await oids_service.get_all_oids()
        return templates.TemplateResponse(
            "printer_oids/list.html",
            {
                "request": request,
                "oids_configs": oids_configs
            }
        )
    except Exception as e:
        logger.error(f"Error listando configuraciones OID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=PrinterOIDs)
async def create_printer_oids(data: PrinterOIDsCreate, db: Session = Depends(get_db)):
    """Crea una nueva configuración de OIDs."""
    try:
        logger.info(f"Creando configuración OID para marca: {data.brand}")
        oids_service = PrinterOIDsService(db)
        return await oids_service.create_oids_config(data)
    except Exception as e:
        logger.error(f"Error creando configuración OID: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{oids_id}", response_model=PrinterOIDs)
async def get_printer_oids(oids_id: int, db: Session = Depends(get_db)):
    """Obtiene una configuración específica de OIDs."""
    try:
        logger.info(f"Obteniendo configuración OID {oids_id}")
        oids_service = PrinterOIDsService(db)
        config = await oids_service.get_oids_config(oids_id)
        if not config:
            raise HTTPException(status_code=404, detail="OID configuration not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo configuración OID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{oids_id}", response_model=PrinterOIDs)
async def update_printer_oids(oids_id: int, data: PrinterOIDsUpdate, db: Session = Depends(get_db)):
    """Actualiza una configuración de OIDs."""
    try:
        logger.info(f"Actualizando configuración OID {oids_id}")
        oids_service = PrinterOIDsService(db)
        config = await oids_service.update_oids_config(oids_id, data)
        if not config:
            raise HTTPException(status_code=404, detail="OID configuration not found")
        return config
    except Exception as e:
        logger.error(f"Error actualizando configuración OID: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{oids_id}")
async def delete_printer_oids(oids_id: int, db: Session = Depends(get_db)):
    """Elimina una configuración de OIDs."""
    try:
        logger.info(f"Eliminando configuración OID {oids_id}")
        oids_service = PrinterOIDsService(db)
        if not await oids_service.delete_oids_config(oids_id):
            raise HTTPException(status_code=404, detail="OID configuration not found")
        return {"message": "Configuration deleted successfully"}
    except Exception as e:
        logger.error(f"Error eliminando configuración OID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brand/{brand}", response_model=List[PrinterOIDs])
async def get_oids_by_brand(brand: str, db: Session = Depends(get_db)):
    """Obtiene todas las configuraciones de OIDs para una marca específica."""
    try:
        logger.info(f"Obteniendo configuraciones OID para marca {brand}")
        oids_service = PrinterOIDsService(db)
        configs = await oids_service.get_oids_by_brand(brand)
        return configs
    except Exception as e:
        logger.error(f"Error obteniendo configuraciones OID por marca: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/{oids_id}")
async def test_oids_config(oids_id: int, printer_ip: str, db: Session = Depends(get_db)):
    """Prueba una configuración de OIDs en una impresora específica."""
    try:
        logger.info(f"Probando configuración OID {oids_id} en IP {printer_ip}")
        oids_service = PrinterOIDsService(db)
        result = await oids_service.test_oids_config(oids_id, printer_ip)
        return result
    except Exception as e:
        logger.error(f"Error probando configuración OID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))