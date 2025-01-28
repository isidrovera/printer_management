# app/api/v1/endpoints/drivers.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.driver_service import DriverService
from typing import List
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/test")
async def test_drivers_endpoint():
    return {"message": "Drivers endpoint está funcionando"}

@router.get("/", response_model=List[dict])
async def get_all_drivers(db: Session = Depends(get_db)):
    try:
        driver_service = DriverService(db)
        drivers = await driver_service.get_all()
        
        print(f"GET /drivers - Número de drivers encontrados: {len(drivers) if drivers else 0}")
        
        if not drivers:
            return JSONResponse(content=[], status_code=200)

        driver_list = [
            {
                "id": driver.id,
                "manufacturer": driver.manufacturer,
                "model": driver.model,
                "driver_filename": driver.driver_filename,
                "description": driver.description or "",
            }
            for driver in drivers
        ]

        return driver_list

    except Exception as e:
        print(f"Error en get_all_drivers: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al recuperar drivers: {str(e)}"
        )

@router.get("/{driver_id}", response_model=dict)
async def get_driver_by_id(driver_id: int, db: Session = Depends(get_db)):
    try:
        driver_service = DriverService(db)
        driver = await driver_service.get_by_id(driver_id)
        
        if not driver:
            raise HTTPException(
                status_code=404,
                detail=f"Driver con ID {driver_id} no encontrado"
            )

        return {
            "id": driver.id,
            "manufacturer": driver.manufacturer,
            "model": driver.model,
            "driver_filename": driver.driver_filename,
            "description": driver.description or "",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno al recuperar el driver: {str(e)}"
        )