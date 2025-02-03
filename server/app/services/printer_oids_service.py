# server/app/services/printer_oids_service.py
import logging
from sqlalchemy.orm import Session
from ..db.models.printer_oids import PrinterOIDs
from ..schemas.printer_oids import PrinterOIDsCreate, PrinterOIDsUpdate
from .snmp_service import SNMPService

logger = logging.getLogger(__name__)

class PrinterOIDsService:
    def __init__(self, db: Session):
        self.db = db
        self.snmp_service = SNMPService()

    async def get_all_oids(self):
        """Obtiene todas las configuraciones de OIDs."""
        try:
            logger.debug("Obteniendo todas las configuraciones OID")
            return self.db.query(PrinterOIDs).all()
        except Exception as e:
            logger.error(f"Error obteniendo configuraciones OID: {str(e)}")
            raise

    async def get_oids_config(self, config_id: int):
        """Obtiene una configuración específica de OIDs."""
        try:
            logger.debug(f"Buscando configuración OID {config_id}")
            return self.db.query(PrinterOIDs).filter(PrinterOIDs.id == config_id).first()
        except Exception as e:
            logger.error(f"Error obteniendo configuración OID {config_id}: {str(e)}")
            raise

    async def create_oids_config(self, data: PrinterOIDsCreate):
        """Crea una nueva configuración de OIDs."""
        try:
            logger.info(f"Creando configuración OID para marca {data.brand}")
            config = PrinterOIDs(**data.dict())
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            return config
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando configuración OID: {str(e)}")
            raise

    async def update_oids_config(self, config_id: int, data: PrinterOIDsUpdate):
        """Actualiza una configuración de OIDs."""
        try:
            logger.info(f"Actualizando configuración OID {config_id}")
            config = await self.get_oids_config(config_id)
            if not config:
                return None

            update_data = data.dict(exclude_unset=True)
            for key, value in update_data.items():
                if isinstance(value, dict):
                    current_value = getattr(config, key, {})
                    current_value.update(value)
                    setattr(config, key, current_value)
                else:
                    setattr(config, key, value)

            self.db.commit()
            self.db.refresh(config)
            return config
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando configuración OID {config_id}: {str(e)}")
            raise

    async def delete_oids_config(self, config_id: int):
        """Elimina una configuración de OIDs."""
        try:
            logger.info(f"Eliminando configuración OID {config_id}")
            config = await self.get_oids_config(config_id)
            if config:
                self.db.delete(config)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error eliminando configuración OID {config_id}: {str(e)}")
            raise

    async def get_oids_by_brand(self, brand: str):
        """Obtiene configuraciones de OIDs por marca."""
        try:
            logger.debug(f"Buscando configuraciones OID para marca {brand}")
            return self.db.query(PrinterOIDs).filter(PrinterOIDs.brand == brand).all()
        except Exception as e:
            logger.error(f"Error obteniendo configuraciones OID para marca {brand}: {str(e)}")
            raise

    async def test_oids_config(self, config_id: int, printer_ip: str):
        """Prueba una configuración de OIDs en una impresora."""
        try:
            logger.info(f"Probando configuración OID {config_id} en IP {printer_ip}")
            config = await self.get_oids_config(config_id)
            if not config:
                raise ValueError("Configuración OID no encontrada")

            # Probar cada categoría de OIDs
            test_results = {}
            for category, oids in config.oids.items():
                category_results = {}
                for name, oid in oids.items():
                    if oid:  # Solo probar OIDs definidos
                        try:
                            value = await self.snmp_service.get_oid_value(
                                ip=printer_ip,
                                oid=oid,
                                community=config.snmp_config['community'],
                                version=config.snmp_config['version']
                            )
                            category_results[name] = {
                                'success': True,
                                'value': value
                            }
                        except Exception as e:
                            category_results[name] = {
                                'success': False,
                                'error': str(e)
                            }
                test_results[category] = category_results

            return {
                'config_id': config_id,
                'printer_ip': printer_ip,
                'results': test_results
            }

        except Exception as e:
            logger.error(f"Error probando configuración OID: {str(e)}")
            raise

    def validate_oids_config(self, config):
        """Valida una configuración de OIDs."""
        required_categories = ['system', 'status', 'supplies', 'counters']
        missing_categories = [cat for cat in required_categories if cat not in config.oids]
        
        if missing_categories:
            raise ValueError(f"Faltan categorías requeridas: {', '.join(missing_categories)}")

        # Validar OIDs básicos requeridos
        required_oids = {
            'system': ['name', 'description'],
            'status': ['general'],
            'supplies': ['black'],
            'counters': ['total']
        }

        for category, required in required_oids.items():
            existing = config.oids.get(category, {})
            missing = [oid for oid in required if not existing.get(oid)]
            if missing:
                raise ValueError(f"Faltan OIDs requeridos en {category}: {', '.join(missing)}")
        
        return True