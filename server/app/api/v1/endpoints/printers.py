# server/app/api/v1/endpoints/printers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.driver_service import DriverService  # Actualizamos el import
from app.api.v1.endpoints.websocket import manager
from typing import List, Dict, Any
from app.db.models.printer import Printer
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class PrinterInstallRequest(BaseModel):
    printer_ip: str
    driver_id: int

router = APIRouter()

@router.post("/install/{agent_token}")
async def install_printer(
    agent_token: str,
    install_data: PrinterInstallRequest,
    db: Session = Depends(get_db)
):
    try:
        logger.debug(f"Datos recibidos: printer_ip='{install_data.printer_ip}' driver_id={install_data.driver_id}")
        
        driver_service = DriverService(db)
        
        # Obtener información del driver
        driver_info = await driver_service.get_driver_for_installation(install_data.driver_id)
        logger.debug(f"Información del driver obtenida: {driver_info}")
        
        if not driver_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver no encontrado"
            )
        
        # Preparar datos de la impresora para el comando
        printer_data = {
            "printer_ip": install_data.printer_ip,
            "manufacturer": driver_info["manufacturer"],
            "model": driver_info["model"],
            "driver_url": driver_info["download_url"],
            "driver_filename": driver_info["driver_filename"]
        }
        
        try:
            # Enviar comando al agente
            await manager.send_install_printer_command(agent_token, printer_data)
            logger.info(f"Comando de instalación enviado exitosamente al agente {agent_token}")
            
            return {
                "status": "success",
                "message": "Comando de instalación enviado correctamente",
                "details": {
                    "printer_ip": install_data.printer_ip,
                    "driver": f"{driver_info['manufacturer']} {driver_info['model']}"
                }
            }
            
        except ValueError as ve:
            logger.error(f"Error de validación: {str(ve)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )
        except Exception as e:
            logger.error(f"Error enviando comando al agente: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error enviando comando al agente: {str(e)}"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error crítico en install_printer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
@router.get("/monitored", response_model=List[Dict[str, Any]])
async def get_monitored_printers(
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de impresoras configuradas para monitoreo.
    """
    try:
        query = db.query(Printer).filter(
            Printer.is_active == True
        ).with_entities(
            Printer.ip_address,
            Printer.brand,
            Printer.oid_config_id
        ).all()
        
        printers = []
        for printer in query:
            printer_data = {
                "ip_address": printer.ip_address,
                "brand": printer.brand,
                "oid_config_id": printer.oid_config_id
            }
            printers.append(printer_data)
            
        return printers
        
    except Exception as e:
        logger.error(f"Error getting monitored printers: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/monitored/{agent_id}", response_model=List[Dict[str, Any]])
async def get_agent_printers(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene las impresoras asignadas a un agente específico"""
    try:
        printers = db.query(Printer).filter(
            Printer.agent_id == agent_id,
            Printer.is_active == True
        ).all()
        
        result = []
        for printer in printers:
            printer_data = {
                "ip_address": printer.ip_address,
                "brand": printer.brand,
                "model": printer.model,
                "id": printer.id
            }
            result.append(printer_data)
            
        logger.info(f"Retornando {len(result)} impresoras para el agente {agent_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error obteniendo impresoras del agente {agent_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))




@router.get("/{printer_id}/counters", response_model=Dict[str, Any])
def get_printer_counters(
    printer_id: int, 
    db: Session = Depends(get_db)
):
    """
    Obtiene los contadores de una impresora específica.
    """
    try:
        printer = db.query(Printer).filter(Printer.id == printer_id).first()
        
        if not printer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Impresora con ID {printer_id} no encontrada"
            )
        
        # Extraer contadores del printer_data
        printer_data = printer.printer_data or {}
        counters = printer_data.get('counters', {})
        
        return {
            "printer_id": printer.id,
            "name": printer.name,
            "counters": {
                "total": counters.get('total', 0),
                "color": counters.get('color', 0),
                "black_and_white": counters.get('black_and_white', 0),
                # Agregar más contadores según sea necesario
                "copies": counters.get('copies', 0),
                "prints": counters.get('prints', 0),
                "scans": counters.get('scans', 0)
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo contadores de impresora {printer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener contadores: {str(e)}"
        )

@router.get("/{printer_id}/supplies", response_model=Dict[str, Any])
def get_printer_supplies(
    printer_id: int, 
    db: Session = Depends(get_db)
):
    """
    Obtiene los niveles de suministros de una impresora específica.
    """
    try:
        printer = db.query(Printer).filter(Printer.id == printer_id).first()
        
        if not printer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Impresora con ID {printer_id} no encontrada"
            )
        
        # Extraer suministros del printer_data
        printer_data = printer.printer_data or {}
        supplies = printer_data.get('supplies', {})
        
        return {
            "printer_id": printer.id,
            "name": printer.name,
            "supplies": {
                "toners": {
                    "black": {
                        "level": supplies.get('toners', {}).get('black', {}).get('percentage', 0),
                        "status": supplies.get('toners', {}).get('black', {}).get('status', 'unknown')
                    },
                    "cyan": {
                        "level": supplies.get('toners', {}).get('cyan', {}).get('percentage', 0),
                        "status": supplies.get('toners', {}).get('cyan', {}).get('status', 'unknown')
                    },
                    "magenta": {
                        "level": supplies.get('toners', {}).get('magenta', {}).get('percentage', 0),
                        "status": supplies.get('toners', {}).get('magenta', {}).get('status', 'unknown')
                    },
                    "yellow": {
                        "level": supplies.get('toners', {}).get('yellow', {}).get('percentage', 0),
                        "status": supplies.get('toners', {}).get('yellow', {}).get('status', 'unknown')
                    }
                },
                "drums": {
                    "black": {
                        "level": supplies.get('drums', {}).get('black', {}).get('percentage', 0),
                        "status": supplies.get('drums', {}).get('black', {}).get('status', 'unknown')
                    },
                    "cyan": {
                        "level": supplies.get('drums', {}).get('cyan', {}).get('percentage', 0),
                        "status": supplies.get('drums', {}).get('cyan', {}).get('status', 'unknown')
                    },
                    "magenta": {
                        "level": supplies.get('drums', {}).get('magenta', {}).get('percentage', 0),
                        "status": supplies.get('drums', {}).get('magenta', {}).get('status', 'unknown')
                    },
                    "yellow": {
                        "level": supplies.get('drums', {}).get('yellow', {}).get('percentage', 0),
                        "status": supplies.get('drums', {}).get('yellow', {}).get('status', 'unknown')
                    }
                }
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo suministros de impresora {printer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener suministros: {str(e)}"
        )


@router.get("/monitor", response_model=List[Dict[str, Any]])
async def get_monitored_printers(
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de impresoras para monitoreo con detalles completos.
    """
    try:
        # Cargar impresoras con sus clientes
        printers = db.query(Printer).options(joinedload(Printer.client)).all()
        
        processed_printers = []
        for printer in printers:
            try:
                printer_data = printer.printer_data or {}
                supplies = printer_data.get('supplies', {})
                toners = supplies.get('toners', {})
                
                printer_info = {
                    'id': printer.id,
                    'name': printer.name,
                    'brand': printer.brand,
                    'model': printer.model,
                    'ip_address': printer.ip_address,
                    'status': printer.status,
                    'client': printer.client.name if printer.client else 'Sin cliente',
                    'has_alerts': False,
                    'supplies': {
                        'black': {'level': toners.get('black', {}).get('percentage', 0)},
                        'cyan': {'level': toners.get('cyan', {}).get('percentage', 0)},
                        'magenta': {'level': toners.get('magenta', {}).get('percentage', 0)},
                        'yellow': {'level': toners.get('yellow', {}).get('percentage', 0)}
                    },
                    'counters': {
                        'total': printer_data.get('counters', {}).get('total', 0)
                    }
                }
                
                try:
                    printer_info['has_alerts'] = bool(printer.check_critical_supplies())
                except Exception as e:
                    logger.warning(f"Error verificando suministros críticos para impresora {printer.id}: {e}")

                processed_printers.append(printer_info)
                
            except Exception as e:
                logger.error(f"Error procesando impresora {printer.id}: {str(e)}")
                continue

        return processed_printers
        
    except Exception as e:
        logger.error(f"Error obteniendo impresoras monitoreadas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )