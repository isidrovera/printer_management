# server/app/api/v1/endpoints/web.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.client_service import ClientService
from app.services.agent_service import AgentService
from app.services.driver_service import DriverService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/clients")
async def list_clients(request: Request, db: Session = Depends(get_db)):
    client_service = ClientService(db)
    clients = await client_service.get_all()
    return templates.TemplateResponse(
        "clients/list.html",
        {"request": request, "clients": clients}
    )

@router.get("/clients/create")
async def create_client_form(request: Request):
    return templates.TemplateResponse(
        "clients/form.html",
        {"request": request, "client": None}
    )

@router.get("/clients/{client_id}/edit")
async def edit_client_form(request: Request, client_id: int, db: Session = Depends(get_db)):
    client_service = ClientService(db)
    client = await client_service.get_by_id(client_id)
    return templates.TemplateResponse(
        "clients/form.html",
        {"request": request, "client": client}
    )