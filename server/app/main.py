# server/main.py
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

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
from app.middleware.first_login_middleware import first_login_middleware
from app.services.initial_setup import InitialSetupService
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.api.v1.api import api_router, web_router
from app.db.session import engine, SessionLocal
from app.db.base import Base
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

# Configurar el sistema de archivos necesarios
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = BASE_DIR / "app" / "static"
templates = Jinja2Templates(directory="app/templates")

# Configurar directorios necesarios
os.makedirs(settings.DRIVERS_STORAGE_PATH, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = SessionLocal()
    try:
        logger.info("Iniciando configuración inicial...")
        Base.metadata.create_all(bind=engine)
        await InitialSetupService.run_initial_setup(db)
    except Exception as e:
        logger.error(f"Error en startup: {e}")
    finally:
        db.close()
    yield
    # Shutdown
    logger.info("Cerrando aplicación...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# Middleware para redirigir HTTP a HTTPS en producción
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Middlewares en orden
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://copierconnectremote.com",
        "https://www.copierconnectremote.com"
    ] if os.getenv("ENVIRONMENT") == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_websockets=True  # Importante para WebSocket
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Incluir routers
app.include_router(web_router)
app.include_router(api_router, prefix="/api/v1")

# Configuración de WebSocket
@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando servidor con soporte para WebSocket seguro (WSS)")
    # Aquí puedes agregar cualquier configuración adicional de WebSocket

logger.info("Aplicación inicializada completamente")