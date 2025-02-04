from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.printer_oids import PrinterOIDsService
from app.schemas.printer_oids import (
    PrinterOIDsCreate,
    PrinterOIDsUpdate,
    PrinterOIDsResponse,
    BrandResponse
)

router = APIRouter()

@router.get("/", response_model=List[PrinterOIDsResponse])
def get_printer_oids(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de configuraciones de OIDs de impresoras.
    """
    service = PrinterOIDsService(db)
    return service.get_all(skip=skip, limit=limit)

@router.get("/{oid_id}", response_model=PrinterOIDsResponse)
def get_printer_oids_by_id(
    oid_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene una configuración específica de OIDs por ID.
    """
    service = PrinterOIDsService(db)
    db_oids = service.get_by_id(oid_id)
    if db_oids is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración de OIDs no encontrada"
        )
    return db_oids

@router.post("/", response_model=PrinterOIDsResponse, status_code=status.HTTP_201_CREATED)
def create_printer_oids(
    oid_data: PrinterOIDsCreate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva configuración de OIDs.
    """
    service = PrinterOIDsService(db)
    
    # Verificar si ya existe una configuración para esta marca y familia
    existing = service.get_by_brand_and_family(
        oid_data.brand,
        oid_data.model_family
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una configuración para esta marca y familia de modelos"
        )
    
    return service.create(oid_data)

@router.put("/{oid_id}", response_model=PrinterOIDsResponse)
def update_printer_oids(
    oid_id: int,
    oid_data: PrinterOIDsUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza una configuración de OIDs existente.
    """
    service = PrinterOIDsService(db)
    db_oids = service.update(oid_id, oid_data)
    if db_oids is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración de OIDs no encontrada"
        )
    return db_oids

@router.delete("/{oid_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_printer_oids(
    oid_id: int,
    db: Session = Depends(get_db)
):
    """
    Elimina una configuración de OIDs.
    """
    service = PrinterOIDsService(db)
    try:
        success = service.delete(oid_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuración de OIDs no encontrada"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/brands/", response_model=List[BrandResponse])
def get_brands_and_families(
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de marcas y sus familias de modelos disponibles.
    """
    service = PrinterOIDsService(db)
    brands = service.get_available_brands()
    
    response = []
    for brand in brands:
        model_families = service.get_model_families_by_brand(brand)
        response.append({
            "brand": brand,
            "model_families": model_families
        })
    
    return response