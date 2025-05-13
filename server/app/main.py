# server/main.py

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
# ProxyHeadersMiddleware eliminado por incompatibilidad con starlette>=0.40.0

# Cargar configuración y módulos internos
os.environ["STARLETTE_ENV_FILE"] = ""

from app.core.config import settings
from app.middleware.auth_middleware import auth_middleware
from app.middleware.first_login_middleware import first_login_middleware
from app.services.initial_setup import InitialSetupService
from app.api.v1.api import api_router
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Configuración de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear carpeta de almacenamiento si no existe
os.makedirs(settings.DRIVERS_STORAGE_PATH, exist_ok=True)

# Contexto de vida útil de la aplicación
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

# Inicializar la app FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS
logger.info("🔧 [CONFIG] Configurando middleware CORS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Cambiar a dominios específicos en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Middleware de autenticación personalizado
logger.info("🔐 [CONFIG] Agregando middleware de autenticación")
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

# Middleware para primer login
logger.info("🔄 [CONFIG] Agregando middleware primer login")
app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)

# Rutas de la API
logger.info("📡 [CONFIG] Incluyendo rutas API")
app.include_router(api_router, prefix=settings.API_V1_STR)

logger.info("🚀 [CONFIG] Aplicación completamente inicializada")
