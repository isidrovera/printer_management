from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.printer_oids import PrinterOIDs
from app.schemas.printer_oids import PrinterOIDsCreate, PrinterOIDsUpdate
from app.core.logging import logger

class PrinterOIDsService:
   def __init__(self, db: Session):
       self.db = db

   def get_all(self, skip: int = 0, limit: int = 100) -> List[PrinterOIDs]:
       """Obtiene todos los registros de OIDs de impresoras."""
       logger.info(f"Recuperando registros de OIDs (skip: {skip}, limit: {limit})")
       return self.db.query(PrinterOIDs).offset(skip).limit(limit).all()

   def get_by_id(self, oid_id: int) -> Optional[PrinterOIDs]:
       """Obtiene un registro de OIDs por su ID."""
       logger.info(f"Buscando registro de OIDs con ID: {oid_id}")
       return self.db.query(PrinterOIDs).filter(PrinterOIDs.id == oid_id).first()

   def get_by_brand_and_family(self, brand: str, model_family: str) -> Optional[PrinterOIDs]:
       """Obtiene un registro de OIDs por marca y familia de modelo."""
       logger.info(f"Buscando registro de OIDs para marca: {brand}, familia de modelo: {model_family}")
       return self.db.query(PrinterOIDs).filter(
           PrinterOIDs.brand == brand,
           PrinterOIDs.model_family == model_family
       ).first()

   async def create(self, oid_data: dict) -> PrinterOIDs:
       """Crea un nuevo registro de OIDs."""
       try:
           logger.info(f"Creando nuevo registro de OIDs: {oid_data}")
           db_oids = PrinterOIDs(**oid_data)
           self.db.add(db_oids)
           self.db.commit()
           self.db.refresh(db_oids)
           logger.info(f"Registro de OIDs creado exitosamente con ID: {db_oids.id}")
           return db_oids
       except Exception as e:
           logger.error(f"Error al crear registro de OIDs: {str(e)}")
           self.db.rollback()
           raise

   async def update(self, oid_id: int, oid_data: PrinterOIDsUpdate) -> Optional[PrinterOIDs]:
       """Actualiza un registro de OIDs existente."""
       try:
           logger.info(f"Actualizando registro de OIDs con ID: {oid_id}")
           db_oids = self.get_by_id(oid_id)
           if not db_oids:
               logger.warning(f"Registro de OIDs con ID {oid_id} no encontrado")
               return None
           
           for key, value in oid_data.dict(exclude_unset=True).items():
               setattr(db_oids, key, value)
               
           self.db.commit()
           self.db.refresh(db_oids)
           logger.info(f"Registro de OIDs con ID {oid_id} actualizado exitosamente")
           return db_oids
       except Exception as e:
           logger.error(f"Error al actualizar registro de OIDs: {str(e)}")
           self.db.rollback()
           raise

    def delete(self, oid_id: int) -> bool:
       """Elimina un registro de OIDs."""
       try:
           logger.info(f"Intentando eliminar registro de OIDs con ID: {oid_id}")
           db_oids = self.get_by_id(oid_id)
           if not db_oids:
               logger.warning(f"Registro de OIDs con ID {oid_id} no encontrado")
               return False
           
           # Verificar si hay impresoras usando esta configuración
           if db_oids.printers:
               logger.warning(f"No se puede eliminar OIDs con ID {oid_id}: hay impresoras usando esta configuración")
               raise ValueError("No se puede eliminar: hay impresoras usando esta configuración")
           
           self.db.delete(db_oids)
           self.db.commit()
           logger.info(f"Registro de OIDs con ID {oid_id} eliminado exitosamente")
           return True
       except ValueError as ve:
           logger.error(str(ve))
           raise
       except Exception as e:
           logger.error(f"Error al eliminar registro de OIDs: {str(e)}")
           self.db.rollback()
           raise

   def get_available_brands(self) -> List[str]:
       """Obtiene la lista de marcas disponibles."""
       logger.info("Recuperando lista de marcas disponibles")
       return [r[0] for r in self.db.query(PrinterOIDs.brand).distinct()]

   def get_model_families_by_brand(self, brand: str) -> List[str]:
       """Obtiene las familias de modelos disponibles para una marca."""
       logger.info(f"Recuperando familias de modelos para marca: {brand}")
       return [
           r[0] for r in self.db.query(PrinterOIDs.model_family)
           .filter(PrinterOIDs.brand == brand)
           .distinct()
       ]