from typing import List, Optional
from pydantic import BaseModel

class PrinterOIDsBase(BaseModel):
    brand: str
    model_family: str
    description: Optional[str] = None
    oid_total_pages: Optional[str] = None
    oid_total_color_pages: Optional[str] = None
    oid_total_bw_pages: Optional[str] = None
    oid_black_toner_level: Optional[str] = None
    oid_cyan_toner_level: Optional[str] = None
    oid_magenta_toner_level: Optional[str] = None
    oid_yellow_toner_level: Optional[str] = None
    # ... agregar todos los demás campos OID como opcionales

class PrinterOIDsCreate(PrinterOIDsBase):
    """Schema para crear una nueva configuración de OIDs."""
    pass

class PrinterOIDsUpdate(PrinterOIDsBase):
    """Schema para actualizar una configuración de OIDs existente."""
    brand: Optional[str] = None
    model_family: Optional[str] = None

class PrinterOIDsResponse(PrinterOIDsBase):
    """Schema para la respuesta de configuración de OIDs."""
    id: int
    
    class Config:
        orm_mode = True

class BrandResponse(BaseModel):
    """Schema para la respuesta de marcas y familias de modelos."""
    brand: str
    model_families: List[str]