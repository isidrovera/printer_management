from fastapi import APIRouter, Request, Depends, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from app.db.session import get_db
from app.services.driver_service import DriverService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Cambiar la ruta de la vista de drivers
@router.get("/drivers")
async def list_drivers(request: Request, db: Session = Depends(get_db)):
    """
    Lista todos los drivers disponibles
    """
    try:
        driver_service = DriverService(db)
        drivers = await driver_service.get_all()
        return templates.TemplateResponse(
            "drivers/list.html",
            {
                "request": request,
                "drivers": drivers
            }
        )
    except Exception as e:
        logger.error(f"Error listando drivers: {str(e)}")
        return templates.TemplateResponse(
            "drivers/list.html",
            {
                "request": request,
                "drivers": [],
                "error": str(e)
            }
        )

@router.get("/drivers/create")
async def create_driver_form(request: Request):
    """
    Muestra el formulario para crear un nuevo driver
    """
    return templates.TemplateResponse(
        "drivers/form.html",
        {
            "request": request,
            "driver": None
        }
    )

@router.post("/drivers/create")
async def create_driver(request: Request, db: Session = Depends(get_db)):
    """
    Procesa la creación de un nuevo driver
    """
    try:
        form = await request.form()
        driver_file: UploadFile = form.get("driver_file")
        if not driver_file:
            raise ValueError("Se requiere archivo de driver")

        # Validar el archivo
        if not driver_file.filename:
            raise ValueError("Nombre de archivo inválido")

        # Validar extensión del archivo
        valid_extensions = ['.ppd', '.ps', '.pdf', '.zip']
        file_extension = Path(driver_file.filename).suffix.lower()
        if file_extension not in valid_extensions:
            raise ValueError(f"Extensión de archivo no válida. Permitidas: {', '.join(valid_extensions)}")

        # Leer el archivo como binario
        file_content = await driver_file.read()
        if not file_content:
            raise ValueError("El archivo está vacío")

        # Validar tamaño del archivo (ejemplo: máximo 50MB)
        max_size = 50 * 1024 * 1024  # 50MB en bytes
        if len(file_content) > max_size:
            raise ValueError("El archivo excede el tamaño máximo permitido (50MB)")

        driver_service = DriverService(db)
        driver = await driver_service.create_driver(
            manufacturer=form.get("manufacturer"),
            model=form.get("model"),
            driver_file=file_content,
            filename=driver_file.filename,
            description=form.get("description")
        )

        logger.info(f"Driver creado: {driver.manufacturer} {driver.model}")
        return RedirectResponse("/drivers", status_code=303)
    except ValueError as e:
        logger.warning(f"Error de validación al crear driver: {str(e)}")
        return templates.TemplateResponse(
            "drivers/form.html",
            {
                "request": request,
                "driver": None,
                "error": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error creando driver: {str(e)}")
        return templates.TemplateResponse(
            "drivers/form.html",
            {
                "request": request,
                "driver": None,
                "error": "Error interno al crear el driver"
            }
        )

@router.get("/drivers/{driver_id}/edit")
async def edit_driver_form(request: Request, driver_id: int, db: Session = Depends(get_db)):
    """
    Muestra el formulario para editar un driver existente
    """
    try:
        driver_service = DriverService(db)
        driver = await driver_service.get_by_id(driver_id)
        if not driver:
            return RedirectResponse("/drivers", status_code=303)
        return templates.TemplateResponse(
            "drivers/form.html",
            {
                "request": request,
                "driver": driver
            }
        )
    except Exception as e:
        logger.error(f"Error cargando formulario de edición: {str(e)}")
        return RedirectResponse("/drivers", status_code=303)

@router.post("/drivers/{driver_id}/edit")
async def edit_driver(request: Request, driver_id: int, db: Session = Depends(get_db)):
    """
    Procesa la actualización de un driver existente
    """
    try:
        form = await request.form()
        driver_service = DriverService(db)

        # Preparar datos de actualización
        update_data = {
            "manufacturer": form.get("manufacturer"),
            "model": form.get("model"),
            "description": form.get("description")
        }

        # Verificar si se subió un nuevo archivo
        driver_file = form.get("driver_file")
        if driver_file and driver_file.filename:
            # Validar el nuevo archivo
            file_content = await driver_file.read()
            update_data.update({
                "driver_file": file_content,
                "driver_filename": driver_file.filename
            })

        driver = await driver_service.update(
            driver_id,
            **update_data
        )
        
        logger.info(f"Driver actualizado: {driver.manufacturer} {driver.model}")
        return RedirectResponse("/drivers", status_code=303)
    except Exception as e:
        logger.error(f"Error actualizando driver: {str(e)}")
        return templates.TemplateResponse(
            "drivers/form.html",
            {
                "request": request,
                "driver_id": driver_id,
                "error": str(e)
            }
        )

@router.delete("/drivers/{driver_id}")
async def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    """
    Elimina un driver existente
    """
    try:
        driver_service = DriverService(db)
        driver = await driver_service.get_by_id(driver_id)
        if not driver:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "Driver no encontrado"}
            )
            
        deleted = await driver_service.delete_driver(driver_id)
        if deleted:
            # Intentar eliminar el archivo físico
            try:
                file_path = Path(settings.DRIVERS_STORAGE_PATH) / driver.driver_filename
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"No se pudo eliminar el archivo físico: {str(e)}")

            return JSONResponse(content={"success": True})
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Error al eliminar el driver"}
        )
    except Exception as e:
        logger.error(f"Error eliminando driver: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/drivers/{driver_id}/download")
async def download_driver(driver_id: int, db: Session = Depends(get_db)):
    """
    Descarga un archivo de driver
    """
    try:
        driver_service = DriverService(db)
        driver = await driver_service.get_by_id(driver_id)
        
        if not driver:
            return JSONResponse(
                status_code=404,
                content={"error": "Driver no encontrado"}
            )

        file_path = Path(settings.DRIVERS_STORAGE_PATH) / driver.driver_filename

        if not file_path.exists():
            return JSONResponse(
                status_code=404,
                content={"error": "Archivo no encontrado"}
            )

        return FileResponse(
            path=file_path,
            filename=driver.driver_filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"Error descargando driver: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/drivers/{driver_id}/details")
async def driver_details(request: Request, driver_id: int, db: Session = Depends(get_db)):
    """
    Muestra los detalles de un driver específico
    """
    try:
        driver_service = DriverService(db)
        driver = await driver_service.get_by_id(driver_id)
        
        if not driver:
            return RedirectResponse("/drivers", status_code=303)
            
        # Obtener información adicional como la lista de impresoras que usan este driver
        printers_using = await driver_service.get_printers_using_driver(driver_id)
        
        return templates.TemplateResponse(
            "drivers/details.html",
            {
                "request": request,
                "driver": driver,
                "printers_using": printers_using
            }
        )
    except Exception as e:
        logger.error(f"Error obteniendo detalles del driver: {str(e)}")
        return templates.TemplateResponse(
            "drivers/details.html",
            {
                "request": request,
                "driver": None,
                "error": str(e)
            }
        )

@router.get("/drivers/compatible")
async def get_compatible_drivers(
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene una lista de drivers compatibles basados en fabricante y/o modelo
    """
    try:
        driver_service = DriverService(db)
        drivers = await driver_service.get_compatible_drivers(manufacturer, model)
        return JSONResponse(content={"drivers": drivers})
    except Exception as e:
        logger.error(f"Error buscando drivers compatibles: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )