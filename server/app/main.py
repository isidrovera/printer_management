# server/main.py
import logging
import os
import itsdangerous
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.middleware.auth_middleware import auth_middleware
from app.middleware.first_login_middleware import first_login_middleware
from app.services.initial_setup import InitialSetupService
from app.core.config import settings
from app.api.v1.api import api_router, web_router
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Configuración de logging mejorada
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(settings.LOG_DIR, 'app.log'))
    ]
)
logger = logging.getLogger(__name__)

# Configuración de directorios
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = BASE_DIR / "app" / "static"
templates = Jinja2Templates(directory="app/templates")

# Asegurar directorios necesarios
REQUIRED_DIRS = [
    settings.DRIVERS_STORAGE_PATH,
    settings.LOG_DIR,
    settings.TEMP_DIR
]

for directory in REQUIRED_DIRS:
    os.makedirs(directory, exist_ok=True)
    logger.info(f"Directorio asegurado: {directory}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Iniciando configuración inicial...")
        db = SessionLocal()
        Base.metadata.create_all(bind=engine)
        await InitialSetupService.run_initial_setup(db)
        db.close()
        logger.info("Configuración inicial completada")
    except Exception as e:
        logger.error(f"Error en startup: {str(e)}", exc_info=True)
        raise
    yield
    logger.info("Cerrando aplicación...")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
        docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None
    )

    # Configuración de CORS mejorada
    origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )

    # Middleware de sesión
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        session_cookie="session_id",
        max_age=86400,  # 24 horas
        same_site="lax",
        https_only=settings.ENVIRONMENT == "production"
    )

    # Middlewares de autenticación
    app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
    app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)

    # Montar archivos estáticos
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Incluir routers
    app.include_router(web_router)
    app.include_router(
        api_router,
        prefix="/api/v1"
    )

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.ENVIRONMENT != "production",
        ssl_keyfile=settings.SSL_KEYFILE if settings.USE_SSL else None,
        ssl_certfile=settings.SSL_CERTFILE if settings.USE_SSL else None
    )