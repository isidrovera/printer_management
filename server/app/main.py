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
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine
from app.db.base import Base

logger.info("Starting application...")

app = FastAPI(title=settings.PROJECT_NAME)

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
app.include_router(api_router)

logger.info("Creating database tables...")
Base.metadata.create_all(bind=engine)

logger.info("Application startup completed")