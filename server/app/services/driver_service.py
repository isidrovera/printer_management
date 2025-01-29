# app/services/driver_service.py
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models.printer_driver import PrinterDriver
from app.services.driver_storage import DriverStorage
from pathlib import Path
import os
from fastapi import HTTPException

class DriverService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = DriverStorage()

    async def get_all(self) -> List[PrinterDriver]:
        """Obtiene todos los drivers disponibles."""
        return self.db.query(PrinterDriver).all()

    async def get_by_id(self, driver_id: int) -> Optional[PrinterDriver]:
        """Obtiene un driver específico por ID."""
        driver = self.db.query(PrinterDriver).filter(PrinterDriver.id == driver_id).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver no encontrado")
        return driver

    async def create_driver(
        self, 
        manufacturer: str, 
        model: str, 
        driver_file: bytes, 
        filename: str, 
        description: Optional[str] = None
    ) -> PrinterDriver:
        """Crea un nuevo registro de driver y guarda el archivo asociado."""
        # Validar que no exista un driver con el mismo fabricante y modelo
        existing_driver = self.db.query(PrinterDriver).filter(
            PrinterDriver.manufacturer == manufacturer,
            PrinterDriver.model == model
        ).first()
        if existing_driver:
            raise HTTPException(status_code=400, detail="Ya existe un driver para este fabricante y modelo")

        # Guardar el archivo en el sistema de almacenamiento
        try:
            self.storage.save_driver_file(filename, driver_file)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        # Crear el registro en la base de datos
        driver = PrinterDriver(
            manufacturer=manufacturer,
            model=model,
            driver_filename=filename,
            description=description
        )
        try:
            self.db.add(driver)
            self.db.commit()
            self.db.refresh(driver)
            return driver
        except Exception as e:
            self.db.rollback()
            self.storage.delete_driver_file(filename)  # Limpieza del archivo en caso de error
            raise HTTPException(status_code=500, detail=f"Error al crear el driver: {str(e)}")

    async def update_driver(
        self,
        driver_id: int,
        manufacturer: str,
        model: str,
        description: Optional[str] = None,
        driver_file: Optional[bytes] = None,
        filename: Optional[str] = None
    ) -> PrinterDriver:
        """Actualiza un driver existente. Si se pasa un nuevo archivo, lo reemplaza."""
        driver = await self.get_by_id(driver_id)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver no encontrado")

        # Si se proporciona un nuevo archivo, reemplazar el existente
        if driver_file and filename:
            try:
                self.storage.delete_driver_file(driver.driver_filename)  # Eliminar archivo anterior
                self.storage.save_driver_file(filename, driver_file)  # Guardar nuevo archivo
                driver.driver_filename = filename
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error al actualizar el archivo: {str(e)}")

        # Actualizar los datos del driver
        driver.manufacturer = manufacturer
        driver.model = model
        driver.description = description

        try:
            self.db.commit()
            self.db.refresh(driver)
            return driver
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al actualizar el driver: {str(e)}")

    async def delete_driver(self, driver_id: int) -> bool:
        """Elimina un driver de la base de datos y su archivo asociado."""
        driver = await self.get_by_id(driver_id)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver no encontrado")

        # Eliminar el archivo físico
        self.storage.delete_driver_file(driver.driver_filename)

        # Eliminar el registro en la base de datos
        try:
            self.db.delete(driver)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al eliminar el driver: {str(e)}")

    async def get_driver_for_installation(self, driver_id: int) -> Dict:
        """
        Obtiene toda la información necesaria para instalar un driver.
        """
        # Obtener el driver por ID
        driver = await self.get_by_id(driver_id)
        if not driver:
            raise HTTPException(
                status_code=404,
                detail=f"Driver con ID {driver_id} no encontrado"
            )

        # Validar que el archivo del driver exista
        driver_path = Path(settings.DRIVERS_STORAGE_PATH) / driver.driver_filename
        if not driver_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Archivo del driver {driver.driver_filename} no encontrado en {settings.DRIVERS_STORAGE_PATH}"
            )

        # Construir la URL completa usando la configuración del servidor
        download_url = f"{settings.SERVER_URL}/api/v1/drivers/{driver_id}/download"

        # Retornar la información del driver
        return {
            "driver_name": f"{driver.manufacturer} {driver.model}",
            "download_url": download_url,  # URL completa para descarga
            "manufacturer": driver.manufacturer,
            "model": driver.model,
            "driver_filename": driver.driver_filename,
            "description": driver.description,
        }