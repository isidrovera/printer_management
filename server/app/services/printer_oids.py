#server\app\services\printer_oids.py
from typing import List, Optional, Union, Tuple, Dict
from sqlalchemy.orm import Session
from server.app.db.models.printer_oids import PrinterOIDs
from server.app.schemas.printer_oids import PrinterOIDsCreate, PrinterOIDsUpdate
from server.app.core.logging import logger

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

   async def update(self, oid_id: int, oid_data: Union[PrinterOIDsUpdate, dict]) -> Optional[PrinterOIDs]:
        """Actualiza un registro de OIDs existente."""
        try:
            logger.info(f"Actualizando registro de OIDs con ID: {oid_id}")
            db_oids = self.get_by_id(oid_id)
            if not db_oids:
                logger.warning(f"Registro de OIDs con ID {oid_id} no encontrado")
                return None
            
            # Manejar tanto objetos Pydantic como diccionarios
            if hasattr(oid_data, 'dict'):
                data_dict = oid_data.dict(exclude_unset=True)
            else:
                data_dict = {k: v for k, v in oid_data.items() if v is not None}
            
            for key, value in data_dict.items():
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
       
   async def bulk_import(self, oids_data: List[dict]) -> Dict[str, Union[int, List[str]]]:
        """
        Importa múltiples configuraciones de OIDs desde Excel.
        Retorna estadísticas de la importación y lista de errores.
        """
        try:
            logger.info(f"Iniciando importación masiva de {len(oids_data)} registros")
            stats = {
                "created": 0,
                "updated": 0,
                "errors": []
            }

            for data in oids_data:
                try:
                    # Validar campos requeridos
                    if not data.get('brand') or not data.get('model_family'):
                        error_msg = f"Falta marca o familia de modelo en el registro"
                        logger.warning(error_msg)
                        stats["errors"].append(error_msg)
                        continue

                    # Buscar configuración existente
                    existing = self.get_by_brand_and_family(
                        data['brand'],
                        data['model_family']
                    )

                    if existing:
                        # Actualizar registro existente
                        await self.update(existing.id, data)
                        stats["updated"] += 1
                        logger.info(f"Actualizada configuración para {data['brand']} - {data['model_family']}")
                    else:
                        # Crear nuevo registro
                        await self.create(data)
                        stats["created"] += 1
                        logger.info(f"Creada nueva configuración para {data['brand']} - {data['model_family']}")

                except Exception as e:
                    error_msg = f"Error procesando {data.get('brand', 'Unknown')}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
                    continue

            logger.info(f"Importación completada. Creados: {stats['created']}, Actualizados: {stats['updated']}, Errores: {len(stats['errors'])}")
            return stats

        except Exception as e:
            logger.error(f"Error general en importación masiva: {str(e)}")
            raise

   def prepare_export_data(self) -> List[dict]:
        """
        Prepara los datos para exportación a Excel.
        Retorna una lista de diccionarios con todos los campos.
        """
        try:
            logger.info("Preparando datos para exportación a Excel")
            oids = self.get_all(skip=0, limit=None)
            export_data = []

            for oid in oids:
                oid_dict = {
                    # Información Básica
                    "brand": oid.brand,
                    "model_family": oid.model_family,
                    "description": oid.description,
                    
                    # Contadores de Páginas
                    "oid_total_pages": oid.oid_total_pages,
                    "oid_total_color_pages": oid.oid_total_color_pages,
                    "oid_total_bw_pages": oid.oid_total_bw_pages,
                    "oid_total_copies": oid.oid_total_copies,
                    
                    # Tóner
                    "oid_black_toner_level": oid.oid_black_toner_level,
                    "oid_cyan_toner_level": oid.oid_cyan_toner_level,
                    "oid_magenta_toner_level": oid.oid_magenta_toner_level,
                    "oid_yellow_toner_level": oid.oid_yellow_toner_level,
                    
                    # Unidades de Imagen
                    "oid_black_drum_level": oid.oid_black_drum_level,
                    "oid_cyan_drum_level": oid.oid_cyan_drum_level,
                    "oid_magenta_drum_level": oid.oid_magenta_drum_level,
                    "oid_yellow_drum_level": oid.oid_yellow_drum_level,
                    
                    # Otros Consumibles
                    "oid_fuser_unit_level": oid.oid_fuser_unit_level,
                    "oid_transfer_belt_level": oid.oid_transfer_belt_level,
                    "oid_waste_toner_level": oid.oid_waste_toner_level,
                    "oid_waste_toner_max": oid.oid_waste_toner_max,
                    
                    # Bandejas
                    "oid_tray1_level": oid.oid_tray1_level,
                    "oid_tray1_max_capacity": oid.oid_tray1_max_capacity,
                    "oid_tray1_status": oid.oid_tray1_status,
                    "oid_tray1_paper_size": oid.oid_tray1_paper_size,
                    "oid_tray1_paper_type": oid.oid_tray1_paper_type,
                    
                    "oid_tray2_level": oid.oid_tray2_level,
                    "oid_tray2_max_capacity": oid.oid_tray2_max_capacity,
                    "oid_tray2_status": oid.oid_tray2_status,
                    "oid_tray2_paper_size": oid.oid_tray2_paper_size,
                    "oid_tray2_paper_type": oid.oid_tray2_paper_type,
                    
                    "oid_tray3_level": oid.oid_tray3_level,
                    "oid_tray3_max_capacity": oid.oid_tray3_max_capacity,
                    "oid_tray3_status": oid.oid_tray3_status,
                    "oid_tray3_paper_size": oid.oid_tray3_paper_size,
                    "oid_tray3_paper_type": oid.oid_tray3_paper_type,
                    
                    "oid_bypass_tray_level": oid.oid_bypass_tray_level,
                    "oid_bypass_tray_status": oid.oid_bypass_tray_status,
                    
                    # Información del Sistema
                    "oid_printer_status": oid.oid_printer_status,
                    "oid_printer_model": oid.oid_printer_model,
                    "oid_serial_number": oid.oid_serial_number,
                    "oid_firmware_version": oid.oid_firmware_version,
                    "oid_system_contact": oid.oid_system_contact,
                    "oid_system_name": oid.oid_system_name,
                }
                export_data.append(oid_dict)

            logger.info(f"Preparados {len(export_data)} registros para exportación")
            return export_data

        except Exception as e:
            logger.error(f"Error preparando datos para exportación: {str(e)}")
            raise