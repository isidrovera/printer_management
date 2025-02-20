# server/main.py
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Importaciones locales
from app.core.config import settings
from app.middleware.auth_middleware import auth_middleware
from app.middleware.first_login_middleware import first_login_middleware
from app.services.initial_setup import InitialSetupService
from app.api.v1.api import api_router, web_router
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de directorios
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = BASE_DIR / "app" / "static"
templates = Jinja2Templates(directory="app/templates")

# Asegurar que existan los directorios necesarios
os.makedirs(settings.DRIVERS_STORAGE_PATH, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configuración de inicio y cierre de la aplicación"""
    # Startup
    logger.info("Iniciando aplicación...")
    db = SessionLocal()
    try:
        # Crear tablas en la base de datos
        logger.info("Verificando estructura de base de datos...")
        Base.metadata.create_all(bind=engine)
        
        # Ejecutar configuración inicial
        logger.info("Ejecutando configuración inicial...")
        await InitialSetupService.run_initial_setup(db)
        
        logger.info("Aplicación iniciada correctamente")
    except Exception as e:
        logger.error(f"Error en el inicio de la aplicación: {e}")
        raise
    finally:
        db.close()
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación...")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# Configuración de middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- Permitir cualquier origen temporalmente
    allow_credentials=True,
    allow_methods=["*"],  # <-- Permitir todos los métodos HTTP
    allow_headers=["*"],  # <-- Permitir todos los headers
    expose_headers=["*"]
)


app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)

# Montar archivos estáticos
app.mount(
    "/static",
    StaticFiles(directory=str(static_dir), check_dir=True),
    name="static"
)

# Incluir routers
app.include_router(web_router)
app.include_router(
    api_router,
    prefix=settings.API_V1_STR
)

# Configuración de templates
templates.env.filters['numberformat'] = lambda value: "{:,}".format(value)
templates.env.filters['default'] = lambda value, default_value: value if value is not None else default_value

logger.info("Aplicación inicializada completamente")