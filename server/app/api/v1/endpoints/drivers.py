# app/api/v1/endpoints/drivers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.app.db.session import get_db
from server.app.services.driver_service import DriverService
from typing import List
import os
from fastapi.responses import FileResponse  # Agregar este import
from server.app.core.config import settings
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

router = APIRouter()

@router.get("/test")  # Será accesible en /api/v1/drivers/test
async def test_drivers_endpoint():
    return JSONResponse(
        content={"message": "Drivers endpoint está funcionando"},
        headers={"Content-Type": "application/json"}
    )

@router.get("/")
async def get_all_drivers(db: Session = Depends(get_db)):
    try:
        print("Endpoint drivers llamado")
        driver_service = DriverService(db)
        drivers = await driver_service.get_all()
        
        driver_list = jsonable_encoder([
            {
                "id": driver.id,
                "manufacturer": driver.manufacturer,
                "model": driver.model,
                "driver_filename": driver.driver_filename,
                "description": driver.description or "",
            }
            for driver in drivers
        ])
        
        return JSONResponse(
            content=driver_list,
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        print(f"Error en get_all_drivers: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
            headers={"Content-Type": "application/json"}
        )

@router.get("/{driver_id}")  # Será accesible en /api/v1/drivers/{driver_id}
async def get_driver_by_id(driver_id: int, db: Session = Depends(get_db)):
    try:
        driver_service = DriverService(db)
        driver = await driver_service.get_by_id(driver_id)
        
        if not driver:
            return JSONResponse(
                status_code=404,
                content={"detail": f"Driver con ID {driver_id} no encontrado"},
                headers={"Content-Type": "application/json"}
            )

        driver_data = jsonable_encoder({
            "id": driver.id,
            "manufacturer": driver.manufacturer,
            "model": driver.model,
            "driver_filename": driver.driver_filename,
            "description": driver.description or "",
        })

        return JSONResponse(
            content=driver_data,
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
            headers={"Content-Type": "application/json"}
        )

@router.delete("/{driver_id}")  # Será accesible en /api/v1/drivers/{driver_id}
async def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    """
    Elimina un driver por su ID.
    """
    try:
        driver_service = DriverService(db)
        # Asegúrate de usar "await" porque delete_driver es asíncrono
        success = await driver_service.delete_driver(driver_id)
        
        if success:
            return JSONResponse(
                status_code=200,
                content={"detail": f"Driver con ID {driver_id} eliminado correctamente"},
                headers={"Content-Type": "application/json"}
            )
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail},
            headers={"Content-Type": "application/json"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error al eliminar el driver: {str(e)}"},
            headers={"Content-Type": "application/json"}
        )
@router.get("/agents/drivers/download/{driver_id}")  # Ruta exacta que coincide con la URL del agente
async def download_driver_agent(driver_id: int, db: Session = Depends(get_db)):
    try:
        driver_service = DriverService(db)
        driver = await driver_service.get_by_id(driver_id)
        
        if not driver:
            raise HTTPException(status_code=404, detail="Driver no encontrado")
            
        file_path = os.path.join(settings.DRIVERS_STORAGE_PATH, driver.driver_filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Archivo del driver no encontrado")
            
        return FileResponse(
            path=file_path,
            filename=driver.driver_filename,
            media_type='application/zip'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))