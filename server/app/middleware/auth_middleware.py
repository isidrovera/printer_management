# server/app/middleware/auth_middleware.py
from fastapi import Request
from fastapi.responses import JSONResponse
import logging
from app.core.auth import get_current_user
import jwt
from jose import JWTError
from app.core.config import settings

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    logger.debug(f"[AUTH] Iniciando middleware para ruta: {request.url.path}")

    # Lista de rutas públicas que no requieren autenticación
    public_paths = [
        "/api/v1/auth/login",
        "/api/v1/auth/token",
        "/api/v1/ws/agent",
        "/api/v1/monitor/printers",
        "/api/v1/printer-oids",
        "/api/v1/agents/register",
        "/api/v1/monitor/printers/update",
        "/api/v1/agents/drivers/download",
        "/api/v1/drivers/download",
        "/favicon.ico",
        "/static"
    ]

    # Verificar si la ruta es pública
    if any(request.url.path.startswith(path) for path in public_paths):
        logger.debug(f"[AUTH] Ruta pública permitida: {request.url.path}")
        return await call_next(request)

    try:
        # Obtener y validar el token del header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(f"[AUTH] Token no proporcionado o formato inválido: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Token de autenticación no proporcionado o inválido"})