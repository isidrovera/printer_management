# server/main.py

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
# from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware  # Opcional si deseas redirigir a HTTPS manualmente

# Cargar configuración y componentes internos
os.environ["STARLETTE_ENV_FILE"] = ""

from app.core.config import settings
from app.middleware.auth_middleware import auth_middleware
from app.middleware.first_login_middleware import first_login_middleware
from app.services.initial_setup import InitialSetupService
from app.api.v1.api import api_router
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Configuración de logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear carpeta de almacenamiento si no existe
os.makedirs(settings.DRIVERS_STORAGE_PATH, exist_ok=True)

# Contexto de vida útil de la app
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

# Inicialización de FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# 🔐 Middleware para confiar en cabeceras del proxy (X-Forwarded-Proto)
logger.info("🌐 [CONFIG] Configurando ProxyHeadersMiddleware")
app.add_middleware(ProxyHeadersMiddleware)

# 🔒 Opcional: Middleware para restringir dominios permitidos
# logger.info("🌍 [CONFIG] Configurando TrustedHostMiddleware")
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=[
#     "copierconnectremote.com",
#     "*.copierconnectremote.com",
#     "localhost"
# ])

# 🔄 Opcional: Redirigir automáticamente HTTP a HTTPS (si no se maneja por el proxy)
# app.add_middleware(HTTPSRedirectMiddleware)

# 🌍 Middleware CORS global
logger.info("🔧 [CONFIG] Configurando middleware CORS")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 🔐 Middleware de autenticación
logger.info("🔐 [CONFIG] Agregando middleware de autenticación")
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

# 👤 Middleware para primer login
logger.info("🔄 [CONFIG] Agregando middleware primer login")
app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)

# 📡 Rutas API versionadas
logger.info("📡 [CONFIG] Incluyendo rutas API")
app.include_router(api_router, prefix=settings.API_V1_STR)

logger.info("🚀 [CONFIG] Aplicación completamente inicializada")
