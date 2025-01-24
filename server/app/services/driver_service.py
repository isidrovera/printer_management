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
       return self.db.query(PrinterDriver).all()

   async def get_by_id(self, driver_id: int) -> Optional[PrinterDriver]:
       return self.db.query(PrinterDriver).filter(PrinterDriver.id == driver_id).first()

   async def store_driver(self, manufacturer: str, model: str, 
                        driver_file: bytes, driver_inf: str = None, 
                        description: str = None) -> PrinterDriver:
       driver = PrinterDriver(
           manufacturer=manufacturer,
           model=model,
           driver_file=driver_file,
           driver_inf=driver_inf,
           description=description
       )
       self.db.add(driver)
       self.db.commit()
       self.db.refresh(driver)
       return driver

       except Exception as e:
           self.db.rollback()
           raise

   async def update(self, driver_id: int, manufacturer: str, model: str, 
                   description: str = None) -> PrinterDriver:
       driver = await self.get_by_id(driver_id)
       if not driver:
           raise ValueError("Driver no encontrado")
       
       driver.manufacturer = manufacturer
       driver.model = model
       driver.description = description
       
       self.db.commit()
       self.db.refresh(driver)
       return driver

   async def delete(self, driver_id: int) -> bool:
       driver = await self.get_by_id(driver_id)
       if driver:
           self.db.delete(driver)
           self.db.commit()
           return True
       return False

   async def _find_inf_path(self, driver_bytes: bytes) -> str:
       with tempfile.NamedTemporaryFile() as tmp:
           tmp.write(driver_bytes)
           tmp.flush()
           
           with zipfile.ZipFile(tmp.name) as z:
               inf_files = [f for f in z.namelist() if f.lower().endswith('.inf')]
               if not inf_files:
                   raise ValueError("No se encontró archivo .inf en el paquete")
               return inf_files[0]