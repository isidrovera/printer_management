# server/app/services/printer_driver_service.py
import os
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from app.db.models.printer_driver import PrinterDriver

class PrinterDriverService:
   def __init__(self, db: Session):
       self.db = db
       self.drivers_path = "app/static/drivers"  # Directorio donde se guardarán los drivers

   async def get_drivers(self) -> List[PrinterDriver]:
       """Obtiene todos los drivers disponibles."""
       return self.db.query(PrinterDriver).all()

   async def get_driver_by_id(self, driver_id: int) -> Optional[PrinterDriver]:
       """Obtiene un driver específico por ID."""
       driver = self.db.query(PrinterDriver).filter(
           PrinterDriver.id == driver_id
       ).first()
       
       if not driver:
           raise HTTPException(
               status_code=404,
               detail=f"No se encontró driver con ID {driver_id}"
           )
       
       return driver

   async def get_driver(self, manufacturer: str, model: str) -> Optional[PrinterDriver]:
       """Obtiene un driver específico por fabricante y modelo."""
       driver = self.db.query(PrinterDriver).filter(
           PrinterDriver.manufacturer == manufacturer,
           PrinterDriver.model == model
       ).first()
       
       if not driver:
           raise HTTPException(
               status_code=404,
               detail=f"No se encontró driver para {manufacturer} {model}"
           )
       
       return driver

   async def get_driver_path(self, driver: PrinterDriver) -> str:
       """Obtiene la ruta completa del archivo del driver."""
       driver_path = os.path.join(self.drivers_path, driver.driver_filename)
       if not os.path.exists(driver_path):
           raise HTTPException(
               status_code=404,
               detail=f"Archivo de driver no encontrado: {driver.driver_filename}"
           )
       return driver_path

   async def get_driver_info(self, driver: PrinterDriver) -> Dict:
       """Obtiene la información necesaria para la instalación del driver."""
       return {
           "driver_name": f"{driver.manufacturer} {driver.model}",
           "driver_path": await self.get_driver_path(driver),
           "manufacturer": driver.manufacturer,
           "model": driver.model,
           "description": driver.description
       }

   async def get_driver_for_installation(self, driver_id: int) -> Dict:
       """
       Obtiene toda la información necesaria para instalar un driver.
       """
       driver = await self.get_driver_by_id(driver_id)
       
       # Verificar la existencia del archivo
       file_path = await self.get_driver_path(driver)
       
       return {
           "driver_name": f"{driver.manufacturer} {driver.model}",
           "driver_path": file_path,
           "manufacturer": driver.manufacturer,
           "model": driver.model,
           "driver_filename": driver.driver_filename,
           "description": driver.description
       }

   async def get_manufacturers(self) -> List[str]:
       """Obtiene la lista de fabricantes disponibles."""
       manufacturers = self.db.query(PrinterDriver.manufacturer)\
                         .distinct()\
                         .order_by(PrinterDriver.manufacturer)\
                         .all()
       return [m[0] for m in manufacturers]

   async def get_models(self, manufacturer: str) -> List[str]:
       """Obtiene la lista de modelos disponibles para un fabricante."""
       models = self.db.query(PrinterDriver.model)\
                   .filter(PrinterDriver.manufacturer == manufacturer)\
                   .order_by(PrinterDriver.model)\
                   .all()
       return [m[0] for m in models]

   async def create_driver(
       self, 
       manufacturer: str, 
       model: str, 
       driver_filename: str,
       description: str = None
   ) -> PrinterDriver:
       """
       Crea un nuevo registro de driver.
       Verifica que el archivo exista antes de crear el registro.
       """
       # Verificar que el archivo exista en el directorio de drivers
       file_path = os.path.join(self.drivers_path, driver_filename)
       if not os.path.exists(file_path):
           raise HTTPException(
               status_code=400,
               detail=f"El archivo {driver_filename} no existe en el directorio de drivers"
           )

       try:
           # Verificar que no exista un driver para el mismo fabricante y modelo
           existing_driver = await self.get_driver(manufacturer, model)
           if existing_driver:
               raise HTTPException(
                   status_code=400,
                   detail=f"Ya existe un driver para {manufacturer} {model}"
               )
       except HTTPException as e:
           # Si el error es 404 (no encontrado) significa que podemos continuar
           if e.status_code != 404:
               raise e

       driver = PrinterDriver(
           manufacturer=manufacturer,
           model=model,
           driver_filename=driver_filename,
           description=description
       )
       
       try:
           self.db.add(driver)
           self.db.commit()
           self.db.refresh(driver)
           return driver
       except Exception as e:
           self.db.rollback()
           raise HTTPException(
               status_code=500,
               detail=f"Error al crear el driver: {str(e)}"
           )

   async def update_driver(
       self,
       driver_id: int,
       data: Dict
   ) -> PrinterDriver:
       """
       Actualiza un driver existente.
       Solo actualiza los campos proporcionados en data.
       """
       driver = self.db.query(PrinterDriver).filter(PrinterDriver.id == driver_id).first()
       if not driver:
           raise HTTPException(
               status_code=404,
               detail="Driver no encontrado"
           )

       # Si se actualiza el archivo del driver, verificar que exista
       if 'driver_filename' in data:
           file_path = os.path.join(self.drivers_path, data['driver_filename'])
           if not os.path.exists(file_path):
               raise HTTPException(
                   status_code=400,
                   detail=f"El archivo {data['driver_filename']} no existe en el directorio de drivers"
               )

       try:
           for key, value in data.items():
               if hasattr(driver, key):
                   setattr(driver, key, value)
           
           self.db.commit()
           self.db.refresh(driver)
           return driver
       except Exception as e:
           self.db.rollback()
           raise HTTPException(
               status_code=500,
               detail=f"Error al actualizar el driver: {str(e)}"
           )

   async def delete_driver(self, driver_id: int) -> bool:
       """
       Elimina un driver de la base de datos.
       No elimina el archivo físico del driver.
       """
       driver = self.db.query(PrinterDriver).filter(PrinterDriver.id == driver_id).first()
       if not driver:
           raise HTTPException(
               status_code=404,
               detail="Driver no encontrado"
           )

       try:
           self.db.delete(driver)
           self.db.commit()
           return True
       except Exception as e:
           self.db.rollback()
           raise HTTPException(
               status_code=500,
               detail=f"Error al eliminar el driver: {str(e)}"
           )