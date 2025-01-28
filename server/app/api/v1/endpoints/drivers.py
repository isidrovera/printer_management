from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.driver_service import DriverService
from typing import List
from fastapi.responses import JSONResponse

# Crear el enrutador para los endpoints de drivers
router = APIRouter()

@router.get("", response_model=List[dict])  # Cambiado de "/drivers" a ""
def get_all_drivers(db: Session = Depends(get_db)):
    """
    Endpoint para obtener todos los drivers disponibles.
    """
    try:
        driver_service = DriverService(db)
        drivers = driver_service.get_all()

        if not drivers:
            return JSONResponse(content=[], status_code=200)

        # Estructurar los datos para el frontend
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
        # Manejo de errores más detallado
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al recuperar drivers: {str(e)}"
        )

# Puedes agregar más endpoints relacionados con drivers aquí si los necesitas
@router.get("/{driver_id}", response_model=dict)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """
    Endpoint para obtener un driver específico por ID.
    """
    try:
        driver_service = DriverService(db)
        driver = driver_service.get_by_id(driver_id)

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