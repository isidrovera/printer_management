# server/main.py
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

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
    logger.info("🔄 [LIFESPAN] Starting application...")
    db = SessionLocal()
    try:
        logger.info("🔍 [LIFESPAN] Verifying database structure...")
        Base.metadata.create_all(bind=engine)

        logger.info("🚀 [LIFESPAN] Running initial setup...")
        await InitialSetupService.run_initial_setup(db)

        logger.info("✅ [LIFESPAN] Application started successfully")
    except Exception as e:
        logger.error(f"❌ [LIFESPAN] Error during application startup: {e}")
        raise
    finally:
        db.close()

    yield

    logger.info("🛑 [LIFESPAN] Shutting down application...")

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS configuration definitiva (ajustar luego al origen específico)
logger.info("🔧 [CONFIG] Aplicando configuración de CORS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],             # 👈 permite cualquier origen temporalmente
    allow_credentials=True,
    allow_methods=["*"],             # 👈 permite todos los métodos
    allow_headers=["*"],             # 👈 permite todas las cabeceras
)

# Middleware personalizado con manejo explícito de OPTIONS
async def middleware_wrapper(request: Request, call_next, middleware_func):
    if request.method == "OPTIONS":
        logger.debug(f"🌐 [MIDDLEWARE] OPTIONS request permitido automáticamente para ruta {request.url.path}")
        return Response(status_code=200)
    return await middleware_func(request, call_next)

# Middleware de autenticación con logs detallados
async def custom_auth_middleware(request: Request, call_next):
    logger.debug(f"🔐 [AUTH MIDDLEWARE] Ruta solicitada: {request.url.path}")
    return await middleware_wrapper(request, call_next, auth_middleware)

# Middleware para primer inicio de sesión con logs detallados
async def custom_first_login_middleware(request: Request, call_next):
    logger.debug(f"🔄 [FIRST LOGIN MIDDLEWARE] Ruta solicitada: {request.url.path}")
    return await middleware_wrapper(request, call_next, first_login_middleware)

# Agregar middlewares personalizados (con manejo OPTIONS integrado)
app.add_middleware(BaseHTTPMiddleware, dispatch=custom_auth_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=custom_first_login_middleware)

# Include API router
logger.info("📡 [CONFIG] Incluyendo API router")
app.include_router(
    api_router,
    prefix=settings.API_V1_STR
)

logger.info("🚀 [CONFIG] Application fully initialized")
