# server/app/middleware/auth_middleware.py
from fastapi import Request
from fastapi.responses import RedirectResponse
import logging
from app.core.auth import get_current_user
import jwt
from jose import JWTError
from app.core.config import settings

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    logger.debug(f"[AUTH] Inicio: {request.url.path}")

    # Excluir WebSockets de autenticación
    if request.scope["type"] == "websocket":
        logger.debug(f"[AUTH] Omitiendo autenticación para WebSocket: {request.url.path}")
        return await call_next(request)

    # Excluir rutas específicas para agentes
    excluded_paths = (
        "/auth/login", 
        "/static/", 
        "/favicon.ico", 
        "/api/v1/ws/",  # Cambiar esto para cubrir todas las rutas WebSocket
        "/api/v1/monitor/printers", 
        "/api/v1/printer-oids/", 
        "/api/v1/agents/register",
        "/api/v1/monitor/printers/update/", 
        "/api/v1/agents/drivers/download/",
        "/api/v1/drivers/download/", 
        "/drivers/"
    )

    if request.url.path.startswith(excluded_paths):
        logger.debug(f"[AUTH] Ruta excluida: {request.url.path}")
        return await call_next(request)

    # Verificar token de autenticación
    token = request.cookies.get("access_token")
    if not token:
        logger.debug("[AUTH] No se encontró token de acceso")
        return RedirectResponse(url="/auth/login", status_code=303)

    try:
        user = await get_current_user(request)
        request.state.user = user

        if user.must_change_password and not request.url.path.startswith("/auth/change-password"):
            logger.debug("[AUTH] Usuario debe cambiar contraseña")
            return RedirectResponse(url="/auth/change-password", status_code=303)
            
    except Exception as e:
        logger.error(f"[AUTH] Error: {str(e)}")
        return RedirectResponse(url="/auth/login", status_code=303)

    return await call_next(request)