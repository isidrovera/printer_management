# server/app/api/v1/endpoints/monitor_printers.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List

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
            if not printer_data:
                raise ValueError("No se proporcionaron datos de la impresora")

            # Valores requeridos
            required_fields = ["name", "model", "ip_address"]
            for field in required_fields:
                if not printer_data.get(field):
                    raise ValueError(f"El campo {field} es requerido")

            # Buscar la impresora por IP
            printer = self.db.query(Printer).filter(
                Printer.ip_address == printer_data["ip_address"]
            ).first()

            # Si no existe, crear una nueva
            if not printer:
                printer = Printer(
                    name=printer_data["name"],
                    model=printer_data["model"],
                    ip_address=printer_data["ip_address"],
                    agent_id=agent_id,
                    status=printer_data.get("status", "offline"),
                    last_update=datetime.utcnow()
                )
                self.db.add(printer)
            
            # Actualizar datos de la impresora
            printer.name = printer_data["name"]
            printer.model = printer_data["model"]
            printer.status = printer_data.get("status", printer.status)
            printer.last_update = datetime.utcnow()

            # Actualizar suministros si se proporcionan
            if "supplies" in printer_data:
                printer.supplies = printer_data["supplies"]

            # Actualizar contadores si se proporcionan
            if "counters" in printer_data:
                printer.counters = printer_data["counters"]

            # Confirmar cambios
            self.db.commit()
            self.db.refresh(printer)

            logger.info(f"Printer data updated successfully for IP: {printer.ip_address}")
            return printer

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating printer data: {str(e)}")
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
        form_data = await request.json()
        monitor_service = PrinterMonitorService(db)
        
        printer_data = {
            "name": form_data.get("name"),
            "model": form_data.get("model"),
            "ip_address": form_data.get("ip_address"),
            "status": "offline",  # Estado inicial
            "supplies": {
                "black": {"level": 100},
                "cyan": {"level": 100},
                "magenta": {"level": 100},
                "yellow": {"level": 100}
            },
            "counters": {
                "total": 0,
                "color": 0,
                "bw": 0
            }
        }
        
        # Usar el método existente para crear/actualizar
        new_printer = monitor_service.update_printer_data(
            agent_id=form_data.get("agent_id", 1),  # ID del agente por defecto
            printer_data=printer_data
        )
        
        return JSONResponse(content={
            "status": "success",
            "printer_id": new_printer.id,
            "message": "Impresora creada exitosamente"
        })
        
    except Exception as e:
        logger.error(f"Error creating printer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))