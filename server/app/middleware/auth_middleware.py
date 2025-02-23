# server/app/middleware/auth_middleware.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from app.core.auth import get_current_user
import jwt
from jose import JWTError
from app.core.config import settings

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    logger.debug(f"[AUTH] Inicio: {request.url.path}")

    # Lista de rutas públicas
    public_paths = {
        "/api/v1/auth/login",
        "/api/v1/auth/token",
        "/api/v1/ws/agent/",
        "/api/v1/monitor/printers",
        "/api/v1/printer-oids/",
        "/api/v1/agents/register",
        "/api/v1/monitor/printers/update/",
        "/api/v1/agents/drivers/download/",
        "/api/v1/drivers/download/",
        "/favicon.ico",
        "/static/"
    }

    # Verificar si la ruta es pública
    if any(request.url.path.startswith(path) for path in public_paths):
        logger.debug(f"[AUTH] Ruta pública: {request.url.path}")
        return await call_next(request)

    # Obtener token del header Authorization
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.warning(f"[AUTH] No se encontró token de autorización para: {request.url.path}")
        return JSONResponse(
            status_code=401,
            content={"detail": "No se proporcionó token de autenticación"}
        )

    try:
        # Extraer token del header "Bearer <token>"
        token = auth_header.split(" ")[1]
        user = await get_current_user(token)
        request.state.user = user

        if user.must_change_password and not request.url.path.startswith("/api/v1/auth/change-password"):
            logger.warning(f"[AUTH] Usuario debe cambiar contraseña: {user.username}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Debe cambiar su contraseña"}
            )

        logger.debug(f"[AUTH] Usuario autenticado: {user.username}")
        return await call_next(request)

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        logger.error(f"[AUTH] Error de token: {str(e)}")
        return JSONResponse(
            status_code=401,
            content={"detail": "Token inválido o expirado"}
        )
    except Exception as e:
        logger.error(f"[AUTH] Error inesperado: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"}
        )