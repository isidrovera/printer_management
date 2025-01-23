# server/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine
from app.db.base import Base

app = FastAPI(
    title=settings.PROJECT_NAME,
    # Permitir todos los orígenes
    root_path="/",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_router, prefix="/api/v1")

# Crear tablas
Base.metadata.create_all(bind=engine)