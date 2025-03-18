# server/app/middleware/auth_middleware.py
from fastapi import Request
from fastapi.responses import JSONResponse, Response
import logging
import jwt
from jose import JWTError
from app.core.auth import get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    logger.debug(f"[AUTH] Iniciando middleware para ruta: {request.url.path}")

    if request.method == "OPTIONS":
        logger.debug("[AUTH] Solicitud OPTIONS permitida con headers explícitos")
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )

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

    if any(request.url.path.startswith(path) for path in public_paths):
        logger.debug(f"[AUTH] Ruta pública permitida: {request.url.path}")
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning(f"[AUTH] Token no proporcionado o formato inválido: {request.url.path}")
        return JSONResponse(
            status_code=401,
            content={"detail": "Token no proporcionado o inválido"}
        )

    token = auth_header.split(" ")[1]

    try:
        current_user = await get_current_user(token)
        request.state.user = current_user
        logger.debug(f"[AUTH] Usuario autenticado: {current_user.username}")

        if current_user.must_change_password and not request.url.path.startswith("/api/v1/auth/change-password"):
            logger.warning(f"[AUTH] Usuario debe cambiar contraseña: {current_user.username}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Debe cambiar contraseña antes de continuar"}
            )

        return await call_next(request)

    except jwt.ExpiredSignatureError:
        logger.warning("[AUTH] Token expirado")
        return JSONResponse(status_code=401, content={"detail": "Token expirado"})

    except (jwt.InvalidTokenError, JWTError):
        logger.warning("[AUTH] Token inválido")
        return JSONResponse(status_code=401, content={"detail": "Token inválido"})

    except Exception as e:
        logger.error(f"[AUTH] Error inesperado: {e}")
        return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})
