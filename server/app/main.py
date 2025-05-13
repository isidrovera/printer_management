# server/main.py

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

os.environ["STARLETTE_ENV_FILE"] = ""

from app.core.config import settings
from app.middleware.auth_middleware import auth_middleware
from app.middleware.first_login_middleware import first_login_middleware
from app.services.initial_setup import InitialSetupService
from app.api.v1.api import api_router
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Logging setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Middleware para redirigir http -> https
class ForceHttpsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        forwarded_proto = request.headers.get('x-forwarded-proto')
        if forwarded_proto == 'http':
            url = request.url.replace(scheme="https")
            return Response(status_code=307, headers={"Location": str(url)})
        return await call_next(request)

# Preparar carpeta de almacenamiento
os.makedirs(settings.DRIVERS_STORAGE_PATH, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔄 Iniciando aplicación...")
    db = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        await InitialSetupService.run_initial_setup(db)
        logger.info("✅ Setup inicial completo")
    except Exception as e:
        logger.error(f"❌ Error al iniciar: {e}")
        raise
    finally:
        db.close()
    yield
    logger.info("🛑 Aplicación finalizada")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# Forzar HTTPS
app.add_middleware(ForceHttpsMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringe esto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Middlewares personalizados
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)

# Rutas API
app.include_router(api_router, prefix=settings.API_V1_STR)

logger.info("🚀 Aplicación lista")
