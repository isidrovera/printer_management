# server/app/api/v1/endpoints/monitor_printers.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.db.models.printer import Printer
from datetime import datetime

from app.db.session import get_db
from app.services.monitor_service import PrinterMonitorService
from app.core.logging import logger

router = APIRouter()

@router.post("/update", response_model=Dict[str, Any])
def update_printer_data(self, agent_id: int, printer_data: Dict[str, Any]) -> Printer:
   """
   Actualiza los datos de una impresora para un agente específico.
   """
   try:
       logger.info(f"Iniciando creación/actualización de impresora con datos: {printer_data}")

       if not printer_data:
           logger.error("No se proporcionaron datos de la impresora")
           raise ValueError("No se proporcionaron datos de la impresora")

       # Validar campos requeridos
       required_fields = ["name", "model", "ip_address"]
       for field in required_fields:
           if not printer_data.get(field):
               logger.error(f"Campo requerido faltante: {field}")
               raise ValueError(f"El campo {field} es requerido")

       # Verificar el cliente si se proporciona
       if printer_data.get("client_id"):
           client = self.db.query(Client).filter(Client.id == int(printer_data["client_id"])).first()
           if not client:
               logger.error(f"Cliente no encontrado con ID: {printer_data['client_id']}")
               raise ValueError(f"Cliente no válido con ID: {printer_data['client_id']}")

       # Buscar la impresora existente por IP
       printer = self.db.query(Printer).filter(
           Printer.ip_address == printer_data["ip_address"]
       ).first()

       logger.info(f"Impresora existente encontrada: {printer is not None}")

       # Si no existe, crear una nueva
       if not printer:
           logger.info("Creando nueva impresora")
           default_printer_data = {
               "counters": {
                   "total": 0,
                   "color": {
                       "total": 0,
                       "cyan": 0,
                       "magenta": 0,
                       "yellow": 0,
                       "black": 0
                   },
                   "black_white": 0,
               },
               "supplies": {
                   "toners": {
                       "black": {
                           "current_level": 100,
                           "max_level": 100,
                           "percentage": 100,
                           "status": "ok"
                       },
                       "cyan": {
                           "current_level": 100,
                           "max_level": 100,
                           "percentage": 100,
                           "status": "ok"
                       },
                       "magenta": {
                           "current_level": 100,
                           "max_level": 100,
                           "percentage": 100,
                           "status": "ok"
                       },
                       "yellow": {
                           "current_level": 100,
                           "max_level": 100,
                           "percentage": 100,
                           "status": "ok"
                       }
                   }
               }
           }

           printer = Printer(
               name=printer_data["name"],
               brand=printer_data["brand"],
               model=printer_data["model"],
               ip_address=printer_data["ip_address"],
               agent_id=agent_id,
               status=printer_data.get("status", "offline"),
               last_check=datetime.utcnow(),
               printer_data=default_printer_data,
               oid_config_id=1  # ID por defecto para PrinterOIDs
           )

           # Asignar cliente si se proporciona
           if printer_data.get("client_id"):
               printer.client_id = int(printer_data["client_id"])
               logger.info(f"Cliente asignado a la nueva impresora: {printer_data['client_id']}")

           self.db.add(printer)
           logger.info(f"Nueva impresora creada con datos: {printer_data}")

       else:
           # Actualizar datos básicos de impresora existente
           logger.info("Actualizando datos básicos de la impresora existente")
           printer.name = printer_data["name"]
           printer.brand = printer_data["brand"]
           printer.model = printer_data["model"]
           printer.status = printer_data.get("status", "offline")
           printer.last_check = datetime.utcnow()

           # Actualizar cliente si se proporciona
           if printer_data.get("client_id"):
               printer.client_id = int(printer_data["client_id"])
               logger.info(f"Cliente actualizado para la impresora: {printer_data['client_id']}")

       # Confirmar cambios
       self.db.commit()
       self.db.refresh(printer)

       logger.info(f"Impresora actualizada exitosamente. ID: {printer.id}, IP: {printer.ip_address}")
       return printer

   except ValueError as ve:
       logger.error(f"Error de validación: {str(ve)}")
       self.db.rollback()
       raise

   except Exception as e:
       logger.error(f"Error inesperado en update_printer_data: {str(e)}")
       self.db.rollback()
       raise
@router.get("/critical-supplies", response_model=List[Dict[str, Any]])
def get_critical_supplies(
    db: Session = Depends(get_db)
):
    """
    Obtiene impresoras con consumibles en estado crítico.
    """
    try:
        monitor_service = PrinterMonitorService(db)
        critical_printers = monitor_service.get_printers_with_critical_supplies()
        return [
            {
                "printer_id": printer.id,
                "printer_name": printer.name,
                "critical_supplies": printer.check_critical_supplies()
            } 
            for printer in critical_printers
        ]
    except Exception as e:
        logger.error(f"Error retrieving critical supplies: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/report", response_model=Dict[str, Any])
def generate_printer_report(
    db: Session = Depends(get_db)
):
    """
    Genera un informe general de impresoras.
    """
    try:
        monitor_service = PrinterMonitorService(db)
        report = monitor_service.generate_printer_report()
        return report
    except Exception as e:
        logger.error(f"Error generating printer report: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{printer_id}/history", response_model=Dict[str, List])
def get_printer_history(
    printer_id: int, 
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de una impresora específica.
    
    - Por defecto recupera el historial de los últimos 7 días
    """
    try:
        monitor_service = PrinterMonitorService(db)
        history = monitor_service.get_printer_history(printer_id, days)
        return history
    except Exception as e:
        logger.error(f"Error retrieving printer history for printer {printer_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
@router.post("/create", response_model=Dict[str, Any])
async def create_printer(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Endpoint para crear una nueva impresora.
    """
    try:
        # Obtener los datos del formulario
        form_data = await request.json()
        logger.info(f"Recibiendo solicitud de creación de impresora con datos: {form_data}")
        
        monitor_service = PrinterMonitorService(db)
        
        # Crear el diccionario con todos los campos necesarios
        printer_data = {}
        
        # Copiar todos los campos necesarios del form_data
        for field in ["name", "brand", "model", "ip_address", "client_id"]:
            if field in form_data:
                printer_data[field] = form_data[field]
                
        # Agregar el estado por defecto
        printer_data["status"] = "offline"
        
        logger.debug(f"Datos de impresora a crear: {printer_data}")
        
        try:
            new_printer = monitor_service.update_printer_data(
                agent_id=form_data.get("agent_id", 1),
                printer_data=printer_data
            )
            
            return {
                "status": "success",
                "printer_id": new_printer.id,
                "message": "Impresora creada exitosamente"
            }
            
        except ValueError as ve:
            logger.error(f"Error de validación al crear impresora: {str(ve)}")
            raise HTTPException(status_code=400, detail=str(ve))
            
    except HTTPException as he:
        raise he
        
    except Exception as e:
        logger.error(f"Error inesperado al crear impresora: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/monitor/printers/{printer_id}")
async def delete_printer(printer_id: int, db: Session = Depends(get_db)):
    try:
        printer = db.query(Printer).filter(Printer.id == printer_id).first()
        if not printer:
            raise HTTPException(status_code=404, detail="Impresora no encontrada")
        
        db.delete(printer)
        db.commit()
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Error eliminando impresora: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/", response_model=List[Dict[str, Any]])
def get_printers(
    db: Session = Depends(get_db),
    agent_id: Optional[int] = None
):
    """
    Obtiene todas las impresoras o las filtradas por agente.
    """
    try:
        logger.info(f"Obteniendo impresoras" + (f" para agente {agent_id}" if agent_id else ""))
        
        monitor_service = PrinterMonitorService(db)
        query = db.query(Printer)
        
        if agent_id:
            query = query.filter(Printer.agent_id == agent_id)
            
        printers = query.all()
        
        return [
            {
                "ip_address": printer.ip_address,
                "brand": printer.brand or "",  # Asegurarse de que no sea None
                "model": printer.model,
                "name": printer.name,
                "status": printer.status,
                "client_id": printer.client_id
            }
            for printer in printers
        ]
        
    except Exception as e:
        logger.error(f"Error obteniendo impresoras: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))