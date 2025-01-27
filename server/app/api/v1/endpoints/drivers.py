from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.driver_service import DriverService
from typing import List

# Crear el enrutador para los endpoints de drivers
router = APIRouter()

@router.get("/drivers", response_model=List[dict])
async def get_all_drivers(db: Session = Depends(get_db)):
    """
    Endpoint para obtener todos los drivers disponibles.
    """
    driver_service = DriverService(db)
    drivers = await driver_service.get_all()

    if not drivers:
        return []

    # Estructurar los datos para el frontend
    driver_list = [
        {
            "id": driver.id,
            "manufacturer": driver.manufacturer,
            "model": driver.model,
            "driver_filename": driver.driver_filename,
            "description": driver.description,
        }
        for driver in drivers
    ]

    return driver_list
