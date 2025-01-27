# app/services/driver_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.printer_driver import PrinterDriver
import tempfile
import zipfile
import os
from pathlib import Path
import logging

class DriverService:
    STORAGE_PATH = "/var/www/printer_drivers"

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def get_all(self) -> List[PrinterDriver]:
        """
        Obtener todos los drivers, con log de errores si ocurre algo.
        """
        try:
            drivers = self.db.query(PrinterDriver).all()
            self.logger.info(f"Recuperados {len(drivers)} drivers")
            return drivers
        except Exception as e:
            self.logger.error(f"Error al recuperar drivers: {e}")
            raise

    def get_by_id(self, driver_id: int) -> Optional[PrinterDriver]:
        return self.db.query(PrinterDriver).filter(PrinterDriver.id == driver_id).first()

    def store_driver(self, manufacturer: str, model: str, driver_file: bytes, filename: str, description: str = None) -> PrinterDriver:
        # Validar si el driver ya existe
        existing_driver = self.db.query(PrinterDriver).filter_by(manufacturer=manufacturer, model=model).first()
        if existing_driver:
            raise ValueError(f"Ya existe un driver para el modelo {model} del fabricante {manufacturer}")

        try:
            os.makedirs(self.STORAGE_PATH, exist_ok=True)
            file_path = Path(self.STORAGE_PATH) / filename

            # Guardar el archivo
            with open(file_path, "wb") as f:
                f.write(driver_file)

            # Crear registro en la base de datos
            driver = PrinterDriver(
                manufacturer=manufacturer,
                model=model,
                driver_filename=filename,
                description=description
            )
            self.db.add(driver)
            self.db.commit()
            self.db.refresh(driver)
            return driver
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)  # Limpieza del archivo en caso de error
            self.db.rollback()
            raise RuntimeError(f"Error al guardar el driver: {e}")

    def update(self, driver_id: int, manufacturer: str, model: str, description: str = None) -> PrinterDriver:
        driver = self.get_by_id(driver_id)
        if not driver:
            raise ValueError("Driver no encontrado")

        driver.manufacturer = manufacturer
        driver.model = model
        driver.description = description

        self.db.commit()
        self.db.refresh(driver)
        return driver

    def delete(self, driver_id: int) -> bool:
        driver = self.get_by_id(driver_id)
        if driver:
            self.db.delete(driver)
            self.db.commit()
            return True
        return False

    def _find_inf_path(self, driver_bytes: bytes) -> List[str]:
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(driver_bytes)
            tmp.flush()
            with zipfile.ZipFile(tmp.name) as z:
                inf_files = [f for f in z.namelist() if f.lower().endswith('.inf')]
                if not inf_files:
                    raise ValueError("No se encontró ningún archivo .inf en el paquete")
                return inf_files