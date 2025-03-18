# server/main.py
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Evita la advertencia de Starlette al no encontrar .env
os.environ["STARLETTE_ENV_FILE"] = ""

# Local imports (corrigiendo la ruta)
from app.core.config import settings
from app.middleware.auth_middleware import auth_middleware
from app.middleware.first_login_middleware import first_login_middleware
from app.services.initial_setup import InitialSetupService
from app.api.v1.api import api_router
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
os.makedirs(settings.DRIVERS_STORAGE_PATH, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown configuration"""
    # Startup
    logger.info("Starting application...")
    db = SessionLocal()
    try:
        # Create database tables
        logger.info("Verifying database structure...")
        Base.metadata.create_all(bind=engine)
        
        # Run initial setup
        logger.info("Running initial setup...")
        await InitialSetupService.run_initial_setup(db)
        
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise
    finally:
        db.close()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS configuration corregida definitivamente
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://161.132.39.159:3000"],
    allow_credentials=True,
    allow_methods=["*"],  # 👈 Cambia aquí: acepta explícitamente todos los métodos
    allow_headers=["Authorization", "Content-Type", "Accept"],  # 👈 ajusta cabeceras explícitas
    expose_headers=["*"]
)


# Add middlewares
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)

# Include API router
app.include_router(
    api_router,
    prefix=settings.API_V1_STR
)

logger.info("Application fully initialized")
