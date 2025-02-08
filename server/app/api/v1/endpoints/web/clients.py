#server/app/api/v1/endpoints/web/clients.py
from fastapi import APIRouter, Request, Depends
from typing import Optional
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
from app.db.session import get_db
from app.services.client_service import ClientService
from app.db.models.client import Client, ClientStatus, ClientType
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/clients")
async def list_clients(
    request: Request, 
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Vista de listado de clientes con opciones de filtrado"""
    try:
        client_service = ClientService(db)
        if search:
            clients = await client_service.search_clients(search)
        elif status:
            clients = await client_service.get_by_status(ClientStatus(status))
        else:
            clients = await client_service.get_all()
            
        return templates.TemplateResponse(
            "clients/list.html",
            {
                "request": request, 
                "clients": clients,
                "statuses": ClientStatus,
                "current_search": search,
                "current_status": status
            }
        )
    except Exception as e:
        logger.error(f"Error listing clients: {str(e)}")
        return templates.TemplateResponse(
            "clients/list.html",
            {"request": request, "clients": [], "error": str(e)}
        )

@router.get("/clients/create")
async def create_client_form(request: Request):
    """Formulario de creación de cliente"""
    return templates.TemplateResponse(
        "clients/form.html",
        {
            "request": request,
            "client": None,
            "client_types": ClientType,
            "client_statuses": ClientStatus
        }
    )

@router.post("/clients/create")
async def create_client(request: Request, db: Session = Depends(get_db)):
    """Procesa la creación de un nuevo cliente"""
    try:
        form = await request.form()
        client_data = {
            "name": form.get("name"),
            "business_name": form.get("business_name"),
            "tax_id": form.get("tax_id"),
            "client_type": form.get("client_type"),
            "contact_name": form.get("contact_name"),
            "contact_email": form.get("contact_email"),
            "contact_phone": form.get("contact_phone"),
            "contact_position": form.get("contact_position"),
            "technical_contact_name": form.get("technical_contact_name"),
            "technical_contact_email": form.get("technical_contact_email"),
            "technical_contact_phone": form.get("technical_contact_phone"),
            "billing_contact_name": form.get("billing_contact_name"),
            "billing_contact_email": form.get("billing_contact_email"),
            "billing_contact_phone": form.get("billing_contact_phone"),
            "billing_address": form.get("billing_address"),
            "billing_city": form.get("billing_city"),
            "billing_state": form.get("billing_state"),
            "billing_zip_code": form.get("billing_zip_code"),
            "billing_country": form.get("billing_country"),
            "service_address": form.get("service_address"),
            "service_city": form.get("service_city"),
            "service_state": form.get("service_state"),
            "service_zip_code": form.get("service_zip_code"),
            "service_country": form.get("service_country"),
            "contract_number": form.get("contract_number"),
            "contract_start_date": form.get("contract_start_date"),
            "contract_end_date": form.get("contract_end_date"),
            "payment_terms": form.get("payment_terms"),
            "credit_limit": form.get("credit_limit"),
            "account_manager": form.get("account_manager"),
            "service_level": form.get("service_level"),
            "support_priority": form.get("support_priority"),
            "status": form.get("status"),
            "notes": form.get("notes")
        }

        client_service = ClientService(db)
        client = await client_service.create(client_data)
        
        logger.info(f"Cliente creado exitosamente: {client.name}")
        return RedirectResponse("/clients", status_code=303)
    
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        return templates.TemplateResponse(
            "clients/form.html",
            {
                "request": request,
                "client": None,
                "error": str(e),
                "client_types": ClientType,
                "client_statuses": ClientStatus,
                "form_data": client_data
            }
        )

@router.get("/clients/{client_id}/edit")
async def edit_client_form(request: Request, client_id: int, db: Session = Depends(get_db)):
    """Formulario de edición de cliente"""
    client_service = ClientService(db)
    client = await client_service.get_by_id(client_id)
    
    if not client:
        return RedirectResponse("/clients", status_code=303)
        
    return templates.TemplateResponse(
        "clients/form.html",
        {
            "request": request,
            "client": client,
            "client_types": ClientType,
            "client_statuses": ClientStatus
        }
    )

@router.post("/clients/{client_id}/edit")
async def edit_client(request: Request, client_id: int, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        
        def clean_value(value):
            if value in ['None', 'none', '', None]:
                return None
            return value

        def parse_date(date_str):
            if not date_str or date_str in ['None', 'none', '']:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return None

        def get_enum_value(enum_class, value):
            if not value:
                return None
            try:
                return enum_class[value.upper()]
            except KeyError:
                return None

        PRIORITY_MAP = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'critical': 4
        }

        try:
            credit_limit = int(float(form.get('credit_limit', 0))) if form.get('credit_limit') else None
        except ValueError:
            credit_limit = None

        client_type = get_enum_value(ClientType, form.get("client_type"))
        status = get_enum_value(ClientStatus, form.get("status"))

        client_data = {
            "name": clean_value(form.get("name")),
            "business_name": clean_value(form.get("business_name")),
            "tax_id": clean_value(form.get("tax_id")),
            "client_type": client_type,
            "status": status,
            "client_code": clean_value(form.get("client_code")),
            "billing_contact_name": clean_value(form.get("billing_contact_name")),
            "billing_contact_email": clean_value(form.get("billing_contact_email")),
            "billing_contact_phone": clean_value(form.get("billing_contact_phone")),
            "billing_address": clean_value(form.get("billing_address")),
            "billing_city": clean_value(form.get("billing_city")),
            "billing_state": clean_value(form.get("billing_state")),
            "billing_zip_code": clean_value(form.get("billing_zip_code")),
            "billing_country": clean_value(form.get("billing_country")),
            "contract_number": clean_value(form.get("contract_number")),
            "contract_start_date": parse_date(form.get("contract_start_date")),
            "contract_end_date": parse_date(form.get("contract_end_date")),
            "service_level": clean_value(form.get("service_level")),
            "payment_terms": clean_value(form.get("payment_terms")),
            "credit_limit": credit_limit,
            "account_manager": clean_value(form.get("account_manager")),
            "support_priority": PRIORITY_MAP.get(form.get('support_priority', '').lower(), 1),
            "notes": clean_value(form.get("notes")),
            "updated_at": datetime.utcnow()
        }

        client_data = {k: v for k, v in client_data.items() if v is not None}

        logger.debug(f"Datos a actualizar para cliente {client_id}: {client_data}")
        
        client_service = ClientService(db)
        client = await client_service.update(client_id, client_data)
        
        if not client:
            raise ValueError("Cliente no encontrado")

        logger.info(f"Cliente {client_id} actualizado exitosamente")
        return RedirectResponse("/clients", status_code=303)
        
    except ValueError as e:
        logger.error(f"Error de validación al actualizar cliente: {str(e)}")
        return templates.TemplateResponse(
            "clients/form.html",
            {
                "request": request,
                "client": {
                    "id": client_id,
                    **form,
                    "contract_start_date": parse_date(form.get("contract_start_date")),
                    "contract_end_date": parse_date(form.get("contract_end_date"))
                },
                "error": str(e),
                "client_types": ClientType,
                "client_statuses": ClientStatus
            }
        )
    except Exception as e:
        logger.error(f"Error al actualizar cliente: {str(e)}")
        return templates.TemplateResponse(
            "clients/form.html",
            {
                "request": request,
                "client": {
                    "id": client_id,
                    **form,
                    "contract_start_date": parse_date(form.get("contract_start_date")),
                    "contract_end_date": parse_date(form.get("contract_end_date"))
                },
                "error": "Error al actualizar el cliente. Por favor, intente nuevamente.",
                "client_types": ClientType,
                "client_statuses": ClientStatus
            }
        )

@router.delete("/clients/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Elimina un cliente"""
    try:
        client_service = ClientService(db)
        deleted = await client_service.delete(client_id)
        
        if deleted:
            return {"success": True}
            
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": "Cliente no encontrado"}
        )
    except Exception as e:
        logger.error(f"Error eliminando cliente: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@router.get("/clients/{client_id}/details")
async def client_details(request: Request, client_id: int, db: Session = Depends(get_db)):
    """Vista detallada de un cliente"""
    client_service = ClientService(db)
    client = await client_service.get_by_id(client_id)
    
    if not client:
        return RedirectResponse("/clients", status_code=303)
        
    return templates.TemplateResponse(
        "clients/details.html",
        {"request": request, "client": client}
    )