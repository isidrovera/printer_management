# app/services/driver_service.py
from typing import List, Optional, BinaryIO
from sqlalchemy.orm import Session
from app.db.models.printer_driver import PrinterDriver
import tempfile
import zipfile

class DriverService:
    def __init__(self, db: Session):
        self.db = db

    async def get_all(self) -> List[PrinterDriver]:
        """
        Devuelve todos los drivers de impresoras.
        """
        return self.db.query(PrinterDriver).all()

    async def get_by_id(self, driver_id: int) -> Optional[PrinterDriver]:
        """
        Devuelve un driver específico por su ID.
        """
        return self.db.query(PrinterDriver).filter(PrinterDriver.id == driver_id).first()

    async def store_driver(self, manufacturer: str, model: str, 
                           driver_file: BinaryIO, description: str = None) -> PrinterDriver:
        """
        Guarda un nuevo driver en la base de datos, leyendo el archivo binario y extrayendo el .inf.
        """
        driver_bytes = driver_file.read()
        inf_path = await self._find_inf_path(driver_bytes)
        
        driver = PrinterDriver(
            manufacturer=manufacturer,
            model=model,
            driver_file=driver_bytes,
            inf_path=inf_path,
            description=description
        )
        self.db.add(driver)
        self.db.commit()
        self.db.refresh(driver)
        return driver

    async def _find_inf_path(self, driver_bytes: bytes) -> str:
        """
        Encuentra el archivo .inf dentro del paquete de drivers.
        """
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(driver_bytes)
            tmp.flush()
            
            with zipfile.ZipFile(tmp.name) as z:
                inf_files = [f for f in z.namelist() if f.endswith('.inf')]
                if not inf_files:
                    raise ValueError("No .inf file found in driver package")
                return inf_files[0]

    async def delete(self, driver_id: int) -> bool:
        """
        Elimina un driver por su ID.
        """
        driver = await self.get_by_id(driver_id)
        if driver:
            self.db.delete(driver)
            self.db.commit()
            return True
        return False
