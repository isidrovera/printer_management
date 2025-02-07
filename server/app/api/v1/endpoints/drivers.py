# app/api/v1/endpoints/drivers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.driver_service import DriverService
from typing import List
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

router = APIRouter()

@router.get("/test")  # Será accesible en /api/v1/drivers/test
async def test_drivers_endpoint():
    return JSONResponse(
        content={"message": "Drivers endpoint está funcionando"},
        headers={"Content-Type": "application/json"}
    )

@router.get("/")  # Será accesible en /api/v1/drivers
async def get_all_drivers(db: Session = Depends(get_db)):
    try:
        print("Endpoint drivers llamado")
        driver_service = DriverService(db)
        drivers = await driver_service.get_all()
        
        print(f"Drivers encontrados: {len(drivers) if drivers else 0}")
        
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
