# server/main.py
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Evita advertencias de Starlette
os.environ["STARLETTE_ENV_FILE"] = ""

from app.core.config import settings
from app.middleware.auth_middleware import auth_middleware
from app.middleware.first_login_middleware import first_login_middleware
from app.services.initial_setup import InitialSetupService
from app.api.v1.api import api_router
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Configuración del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear directorios necesarios
os.makedirs(settings.DRIVERS_STORAGE_PATH, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔄 [LIFESPAN] Iniciando aplicación...")
    db = SessionLocal()
    try:
        logger.info("🔍 [LIFESPAN] Verificando estructura DB...")
        Base.metadata.create_all(bind=engine)

        logger.info("🚀 [LIFESPAN] Ejecutando setup inicial...")
        await InitialSetupService.run_initial_setup(db)

        logger.info("✅ [LIFESPAN] Aplicación iniciada con éxito")
    except Exception as e:
        logger.error(f"❌ [LIFESPAN] Error en arranque: {e}")
        raise
    finally:
        db.close()

    yield

    logger.info("🛑 [LIFESPAN] Cerrando aplicación...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# 👇 Middleware CORS siempre primero (fundamental)
logger.info("🔧 [CONFIG] Configurando middleware CORS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👇 Middlewares personalizados directamente (sin wrapper adicional)
logger.info("🔐 [CONFIG] Agregando middleware de autenticación")
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

logger.info("🔄 [CONFIG] Agregando middleware primer login")
app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)

# Rutas API
logger.info("📡 [CONFIG] Incluyendo rutas API")
app.include_router(api_router, prefix=settings.API_V1_STR)

logger.info("🚀 [CONFIG] Aplicación completamente inicializada")
