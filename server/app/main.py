# server/main.py
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Importaciones locales
from app.core.config import settings
from app.middleware.auth_middleware import auth_middleware
from app.middleware.first_login_middleware import first_login_middleware
from app.middleware.error_handler import error_handler_middleware
from app.middleware.logging_middleware import logging_middleware
from app.services.initial_setup import InitialSetupService
from app.api.v1.api import api_router, web_router
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Configuración de logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(settings.LOGS_STORAGE_PATH, "app.log"),
            encoding="utf-8"
        )
    ]
)
logger = logging.getLogger(__name__)

# Configuración de directorios
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "app" / "static"
templates_dir = BASE_DIR / "app" / "templates"

# Asegurar que existan los directorios necesarios
for directory in [static_dir, templates_dir, Path(settings.DRIVERS_STORAGE_PATH)]:
    directory.mkdir(parents=True, exist_ok=True)

# Configuración de templates
templates = Jinja2Templates(directory=str(templates_dir))

# Filtros personalizados para templates
templates.env.filters['numberformat'] = lambda value: "{:,}".format(value)
templates.env.filters['default'] = lambda value, default_value: value if value is not None else default_value

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configuración de inicio y cierre de la aplicación"""
    # Startup
    logger.info("Iniciando aplicación...")
    db = SessionLocal()
    try:
        # Crear tablas en la base de datos
        logger.info("Verificando estructura de base de datos...")
        Base.metadata.create_all(bind=engine)
        
        # Ejecutar configuración inicial
        logger.info("Ejecutando configuración inicial...")
        await InitialSetupService.run_initial_setup(db)
        
        logger.info("Aplicación iniciada correctamente")
    except Exception as e:
        logger.error(f"Error en el inicio de la aplicación: {e}")
        raise
    finally:
        db.close()
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación...")
    try:
        # Realizar tareas de limpieza si son necesarias
        pass
    except Exception as e:
        logger.error(f"Error en el cierre de la aplicación: {e}")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Configuración de middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else [
        "copierconnectremote.com",
        "www.copierconnectremote.com"
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=error_handler_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)

# Montar archivos estáticos
app.mount(
    "/static",
    StaticFiles(directory=str(static_dir), check_dir=True),
    name="static"
)

# Incluir routers
app.include_router(web_router)
app.include_router(
    api_router,
    prefix=settings.API_V1_STR
)

# Manejador de errores global
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"Error HTTP {exc.status_code}: {exc.detail}")
    return templates.TemplateResponse(
        "errors/error.html",
        {
            "request": request,
            "error_code": exc.status_code,
            "error_message": exc.detail
        },
        status_code=exc.status_code
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Error no manejado: {str(exc)}", exc_info=True)
    return templates.TemplateResponse(
        "errors/500.html",
        {
            "request": request,
            "error_message": str(exc) if settings.DEBUG else "Error interno del servidor"
        },
        status_code=500
    )

# Verificación final de configuración
logger.info(f"Ambiente: {'Desarrollo' if settings.DEBUG else 'Producción'}")
logger.info(f"Documentación API: {settings.SERVER_URL}/api/docs" if settings.DEBUG else "API docs deshabilitados")
logger.info("Aplicación inicializada completamente")