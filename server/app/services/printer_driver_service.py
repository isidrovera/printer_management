# server/app/services/printer_driver_service.py
import os
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models.printer_driver import PrinterDriver

class PrinterDriverService:
    def __init__(self, db: Session):
        self.db = db
        self.drivers_path = "app/static/drivers"  # Directorio donde se guardarán los drivers

    async def get_drivers(self) -> List[PrinterDriver]:
        """Obtiene todos los drivers disponibles."""
        return self.db.query(PrinterDriver).all()

    async def get_driver(self, manufacturer: str, model: str) -> Optional[PrinterDriver]:
        """Obtiene un driver específico por fabricante y modelo."""
        return self.db.query(PrinterDriver).filter(
            PrinterDriver.manufacturer == manufacturer,
            PrinterDriver.model == model
        ).first()

    async def get_driver_path(self, driver: PrinterDriver) -> str:
        """Obtiene la ruta completa del archivo del driver."""
        return os.path.join(self.drivers_path, driver.driver_filename)

    async def get_driver_info(self, driver: PrinterDriver) -> dict:
        """Obtiene la información necesaria para la instalación del driver."""
        return {
            "driver_name": f"{driver.manufacturer} {driver.model}",
            "driver_path": await self.get_driver_path(driver),
            "manufacturer": driver.manufacturer,
            "model": driver.model
        }