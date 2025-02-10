# server/main.py
import logging
import os
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.auth_middleware import auth_middleware
from app.services.initial_setup import InitialSetupService
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.api.v1.api import api_router, web_router
from app.db.session import engine
from app.db.base import Base

logger.info("Starting application...")

app = FastAPI(title=settings.PROJECT_NAME)

# Agregar el middleware de autenticación ANTES del CORS middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

logger.info("Mounting static files...")

# Configurar las plantillas
templates = Jinja2Templates(directory="app/templates")

# Obtener la ruta absoluta del directorio static usando Path
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = BASE_DIR / "app" / "static"

logger.debug(f"Static directory path: {static_dir}")
logger.debug(f"Static directory exists: {static_dir.exists()}")

# Listar archivos en el directorio static/css para debugging
css_dir = static_dir / "css"
if css_dir.exists():
    logger.debug(f"CSS files: {[f.name for f in css_dir.iterdir()]}")

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

logger.info("Including routers...")
# Montar el router web en la raíz
app.include_router(web_router)
# Montar el router API con el prefijo
app.include_router(api_router, prefix="/api/v1")

logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)
# Agregar al final del archivo, antes de "Application startup completed"
@app.on_event("startup")
def startup_event():
    # Crear sesión de base de datos
    db = SessionLocal()
    try:
        logger.info("Verificando configuración inicial de administrador...")
        InitialSetupService.check_and_create_initial_admin(db)
    except Exception as e:
        logger.error(f"Error en configuración inicial de admin: {e}")
    finally:
        db.close()

logger.info("Application startup completed")