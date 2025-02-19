# server/main.py
# server/main.py
import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

# Importaciones locales
from app.core.config import settings
from app.middleware.auth_middleware import auth_middleware
from app.middleware.first_login_middleware import first_login_middleware
from app.services.initial_setup import InitialSetupService
from app.api.v1.api import api_router, web_router
from app.db.session import engine, SessionLocal
from app.db.base import Base

# Configuración de logging
logging.config.dictConfig(settings.LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Configuración de directorios
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = BASE_DIR / "app" / "static"
templates = Jinja2Templates(directory="app/templates")

# Asegurar que existan los directorios necesarios
os.makedirs(settings.DRIVERS_STORAGE_PATH, exist_ok=True)

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

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan
)

# Configuración de middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-Total-Count"]
)

# Middleware para agregar headers de seguridad
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Agregar headers de seguridad
    is_websocket = request.url.path.startswith(f"{settings.API_V1_STR}/ws")
    security_headers = settings.get_security_headers(is_websocket=is_websocket)
    
    for header_name, header_value in security_headers.items():
        response.headers[header_name] = header_value
    
    return response

# Middleware para manejar proxy
@app.middleware("http")
async def proxy_middleware(request: Request, call_next):
    if settings.BEHIND_PROXY and settings.TRUST_PROXY_HEADERS:
        # Confiar en los headers X-Forwarded-* de Nginx/Cloudflare
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        if forwarded_proto:
            request.scope["scheme"] = forwarded_proto
        
        forwarded_host = request.headers.get("X-Forwarded-Host")
        if forwarded_host:
            request.scope["headers"].append(
                (b"host", forwarded_host.encode())
            )
    
    response = await call_next(request)
    return response

# Agregar otros middlewares
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=first_login_middleware)

if not settings.DEBUG:
    # En producción, restringir los hosts permitidos
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=[settings.DOMAIN, f"www.{settings.DOMAIN}"]
    )

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

# Configuración de templates
templates.env.filters['numberformat'] = lambda value: "{:,}".format(value)
templates.env.filters['default'] = lambda value, default_value: value if value is not None else default_value

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=settings.LOGGING_CONFIG
    )