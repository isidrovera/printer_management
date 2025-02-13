# server/main.py
# server/main.py
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

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

# Middleware para WebSocket con Cloudflare
@app.middleware("http")
async def handle_cloudflare_websocket(request: Request, call_next):
    if request.scope["type"] == "websocket":
        # Agregar headers necesarios para WebSocket
        headers = dict(request.scope["headers"])
        headers[b"upgrade"] = b"websocket"
        headers[b"connection"] = b"upgrade"
        request.scope["headers"] = [(k, v) for k, v in headers.items()]
    return await call_next(request)

# Middlewares en orden
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)
app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"]
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Incluir routers
app.include_router(web_router)
app.include_router(api_router, prefix="/api/v1")

logger.info("Aplicación inicializada completamente")