# server/app/api/v1/endpoints/web.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.client_service import ClientService
from app.services.agent_service import AgentService
from app.services.driver_service import DriverService
from fastapi import File, UploadFile
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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

@router.post("/clients/create")
async def create_client(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        name = form.get("name")
        logger.info(f"Creating client with name: {name}")
        
        client_service = ClientService(db)
        await client_service.create(name=name)
        
        logger.info("Client created successfully")
        return RedirectResponse("/clients", status_code=303)
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        return templates.TemplateResponse(
            "clients/form.html",
            {"request": request, "client": None, "error": str(e)}
        )

@router.get("/agents")
async def list_agents(request: Request, db: Session = Depends(get_db)):
    agent_service = AgentService(db)
    agents = await agent_service.get_agents(skip=0, limit=100)
    print(f"Agentes obtenidos: {agents}")  # Debug
    drivers = await agent_service.get_drivers()
    print(f"Drivers obtenidos: {drivers}")  # Debug
    return templates.TemplateResponse(
        "agents/agents.html",
        {"request": request, "agents": agents, "drivers": drivers}
    )




@router.get("/drivers")
async def list_drivers(request: Request, db: Session = Depends(get_db)):
   driver_service = DriverService(db)
   drivers = await driver_service.get_all()
   return templates.TemplateResponse("drivers/list.html", {
       "request": request,
       "drivers": drivers
   })

@router.get("/drivers/create")
async def create_driver_form(request: Request):
   return templates.TemplateResponse("drivers/form.html", {
       "request": request,
       "driver": None
   })

@router.post("/drivers/create")
async def create_driver(request: Request, db: Session = Depends(get_db)):
   try:
       form = await request.form()
       driver_file = form.get("driver_file")
       if not driver_file:
           raise ValueError("Se requiere archivo de driver")

       contents = await driver_file.read()
       driver_service = DriverService(db)
       
       driver = await driver_service.store_driver(
           manufacturer=form.get("manufacturer"),
           model=form.get("model"),
           driver_file=contents,
           description=form.get("description")
       )
       
       logger.info(f"Driver creado: {driver.manufacturer} {driver.model}")
       return RedirectResponse("/drivers", status_code=303)
   except Exception as e:
       logger.error(f"Error creando driver: {str(e)}")
       return templates.TemplateResponse(
           "drivers/form.html",
           {"request": request, "driver": None, "error": str(e)}
       )

@router.get("/drivers/{driver_id}/edit")
async def edit_driver_form(request: Request, driver_id: int, db: Session = Depends(get_db)):
   driver_service = DriverService(db)
   driver = await driver_service.get_by_id(driver_id)
   if not driver:
       return RedirectResponse("/drivers", status_code=303)
   return templates.TemplateResponse("drivers/form.html", {
       "request": request,
       "driver": driver
   })

@router.post("/drivers/{driver_id}/edit") 
async def edit_driver(request: Request, driver_id: int, db: Session = Depends(get_db)):
   try:
       form = await request.form()
       driver_service = DriverService(db)

       driver = await driver_service.update(
           driver_id,
           manufacturer=form.get("manufacturer"),
           model=form.get("model"),
           description=form.get("description")
       )
       
       logger.info(f"Driver actualizado: {driver.manufacturer} {driver.model}")
       return RedirectResponse("/drivers", status_code=303)
   except Exception as e:
       logger.error(f"Error actualizando driver: {str(e)}")
       return templates.TemplateResponse(
           "drivers/form.html",
           {"request": request, "driver_id": driver_id, "error": str(e)}
       )

@router.delete("/drivers/{driver_id}")
async def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    try:
        driver_service = DriverService(db)
        driver = await driver_service.get_by_id(driver_id)
        if not driver:
            return {"success": False, "error": "Driver no encontrado"}, 404
            
        deleted = await driver_service.delete(driver_id)
        return {"success": True} if deleted else {"success": False, "error": "Error al eliminar"}
    except Exception as e:
        logger.error(f"Error eliminando driver: {str(e)}")
        return {"success": False, "error": str(e)}
