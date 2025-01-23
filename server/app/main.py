# server/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.config import settings
from app.api.v1.api import api_router
from app.api.v1.endpoints import web
from app.db.session import engine
from app.db.models.base import Base  # Agrega esta línea

app = FastAPI(title=settings.PROJECT_NAME)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(api_router, prefix="/api/v1")
app.include_router(web.router)

Base.metadata.create_all(bind=engine)