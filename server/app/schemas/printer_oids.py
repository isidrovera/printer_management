from typing import List, Optional
from pydantic import BaseModel

class PrinterOIDsBase(BaseModel):
    brand: str
    model_family: str
    description: Optional[str] = None
    
    # OIDs para contadores de páginas
    oid_total_pages: Optional[str] = None
    oid_total_color_pages: Optional[str] = None
    oid_total_bw_pages: Optional[str] = None
    oid_total_copies: Optional[str] = None
    oid_total_prints: Optional[str] = None
    oid_total_scans: Optional[str] = None
    oid_duplex_pages: Optional[str] = None
    oid_total_faxes: Optional[str] = None
    
    # OIDs para tamaños de papel
    oid_a4_pages: Optional[str] = None
    oid_a3_pages: Optional[str] = None
    oid_letter_pages: Optional[str] = None
    oid_legal_pages: Optional[str] = None
    
    # OIDs para niveles de tóner
    oid_black_toner_level: Optional[str] = None
    oid_cyan_toner_level: Optional[str] = None
    oid_magenta_toner_level: Optional[str] = None
    oid_yellow_toner_level: Optional[str] = None
    
    # OIDs para capacidad máxima de tóner
    oid_black_toner_max: Optional[str] = None
    oid_cyan_toner_max: Optional[str] = None
    oid_magenta_toner_max: Optional[str] = None
    oid_yellow_toner_max: Optional[str] = None
    
    # OIDs para estado de tóner
    oid_black_toner_status: Optional[str] = None
    oid_cyan_toner_status: Optional[str] = None
    oid_magenta_toner_status: Optional[str] = None
    oid_yellow_toner_status: Optional[str] = None
    
    # OIDs para unidades de imagen/drums
    oid_black_drum_level: Optional[str] = None
    oid_cyan_drum_level: Optional[str] = None
    oid_magenta_drum_level: Optional[str] = None
    oid_yellow_drum_level: Optional[str] = None
    
    # OIDs para otros consumibles
    oid_fuser_unit_level: Optional[str] = None
    oid_transfer_belt_level: Optional[str] = None
    oid_waste_toner_level: Optional[str] = None
    oid_waste_toner_max: Optional[str] = None
    
    # OIDs para bandejas de papel
    oid_tray1_level: Optional[str] = None
    oid_tray1_max_capacity: Optional[str] = None
    oid_tray1_status: Optional[str] = None
    oid_tray1_paper_size: Optional[str] = None
    oid_tray1_paper_type: Optional[str] = None
    
    oid_tray2_level: Optional[str] = None
    oid_tray2_max_capacity: Optional[str] = None
    oid_tray2_status: Optional[str] = None
    oid_tray2_paper_size: Optional[str] = None
    oid_tray2_paper_type: Optional[str] = None
    
    oid_tray3_level: Optional[str] = None
    oid_tray3_max_capacity: Optional[str] = None
    oid_tray3_status: Optional[str] = None
    oid_tray3_paper_size: Optional[str] = None
    oid_tray3_paper_type: Optional[str] = None
    
    oid_bypass_tray_level: Optional[str] = None
    oid_bypass_tray_status: Optional[str] = None
    
    # OIDs para información del sistema
    oid_printer_status: Optional[str] = None
    oid_printer_model: Optional[str] = None
    oid_serial_number: Optional[str] = None
    oid_firmware_version: Optional[str] = None
    oid_system_contact: Optional[str] = None
    oid_system_name: Optional[str] = None
    oid_system_location: Optional[str] = None
    oid_printer_memory: Optional[str] = None
    oid_temperature: Optional[str] = None
    oid_display_message: Optional[str] = None
    
    # OIDs para errores y alertas
    oid_error_messages: Optional[str] = None
    oid_warning_messages: Optional[str] = None
    oid_service_messages: Optional[str] = None
    
    # OIDs para información de red
    oid_ip_address: Optional[str] = None
    oid_mac_address: Optional[str] = None
    oid_subnet_mask: Optional[str] = None
    oid_gateway: Optional[str] = None

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