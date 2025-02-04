from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.printer_oids import PrinterOIDs
from app.schemas.printer_oids import PrinterOIDsCreate, PrinterOIDsUpdate

class PrinterOIDsService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[PrinterOIDs]:
        """Obtiene todos los registros de OIDs de impresoras."""
        return self.db.query(PrinterOIDs).offset(skip).limit(limit).all()

    def get_by_id(self, oid_id: int) -> Optional[PrinterOIDs]:
        """Obtiene un registro de OIDs por su ID."""
        return self.db.query(PrinterOIDs).filter(PrinterOIDs.id == oid_id).first()

    def get_by_brand_and_family(self, brand: str, model_family: str) -> Optional[PrinterOIDs]:
        """Obtiene un registro de OIDs por marca y familia de modelo."""
        return self.db.query(PrinterOIDs).filter(
            PrinterOIDs.brand == brand,
            PrinterOIDs.model_family == model_family
        ).first()

    def create(self, oid_data: PrinterOIDsCreate) -> PrinterOIDs:
        """Crea un nuevo registro de OIDs."""
        db_oids = PrinterOIDs(**oid_data.dict())
        self.db.add(db_oids)
        self.db.commit()
        self.db.refresh(db_oids)
        return db_oids

    def update(self, oid_id: int, oid_data: PrinterOIDsUpdate) -> Optional[PrinterOIDs]:
        """Actualiza un registro de OIDs existente."""
        db_oids = self.get_by_id(oid_id)
        if not db_oids:
            return None
            
        for key, value in oid_data.dict(exclude_unset=True).items():
            setattr(db_oids, key, value)
            
        self.db.commit()
        self.db.refresh(db_oids)
        return db_oids

    def delete(self, oid_id: int) -> bool:
        """Elimina un registro de OIDs."""
        db_oids = self.get_by_id(oid_id)
        if not db_oids:
            return False
            
        # Verificar si hay impresoras usando esta configuración
        if db_oids.printers:
            raise ValueError("No se puede eliminar: hay impresoras usando esta configuración")
            
        self.db.delete(db_oids)
        self.db.commit()
        return True

    def get_available_brands(self) -> List[str]:
        """Obtiene la lista de marcas disponibles."""
        return [r[0] for r in self.db.query(PrinterOIDs.brand).distinct()]

    def get_model_families_by_brand(self, brand: str) -> List[str]:
        """Obtiene las familias de modelos disponibles para una marca."""
        return [
            r[0] for r in self.db.query(PrinterOIDs.model_family)
            .filter(PrinterOIDs.brand == brand)
            .distinct()
        ]