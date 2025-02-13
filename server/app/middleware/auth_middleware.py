# server/app/middleware/auth_middleware.py
from fastapi import Request
from fastapi.responses import RedirectResponse
import logging
from app.core.auth import get_current_user
import jwt
from jose import JWTError
from app.core.config import settings

logger = logging.getLogger(__name__)

# Rutas públicas que no requieren autenticación
PUBLIC_PATHS = (
    # Rutas de autenticación y estáticos
    "/auth/login",
    "/static/",
    "/favicon.ico",
    
    # Rutas de WebSocket
    "/api/v1/ws/",
    "/api/v1/ws/agent/",
    "/api/v1/ws/status",
    
    # Rutas de API para agentes
    "/api/v1/agents/register",
    "/api/v1/agents/drivers/download/",
    
    # Rutas de monitoreo e impresoras
    "/api/v1/monitor/printers",
    "/api/v1/monitor/printers/update/",
    "/api/v1/printer-oids/",
    
    # Rutas de drivers
    "/api/v1/drivers/download/",
    "/drivers/"
)

async def auth_middleware(request: Request, call_next):
    logger.debug(f"[AUTH] Inicio: {request.url.path}")

    # Permitir todas las conexiones WebSocket
    if request.scope["type"] == "websocket":
        logger.debug(f"[AUTH] Permitiendo conexión WebSocket: {request.url.path}")
        return await call_next(request)

    # Verificar rutas públicas
    if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
        logger.debug(f"[AUTH] Ruta pública permitida: {request.url.path}")
        return await call_next(request)

    # Verificar token de autenticación
    token = request.cookies.get("access_token")
    if not token:
        logger.debug(f"[AUTH] No se encontró token de acceso para: {request.url.path}")
        return RedirectResponse(url="/auth/login", status_code=303)

    try:
        user = await get_current_user(request)
        request.state.user = user

        if user.must_change_password and not request.url.path.startswith("/auth/change-password"):
            logger.debug(f"[AUTH] Usuario debe cambiar contraseña: {user.username}")
            return RedirectResponse(url="/auth/change-password", status_code=303)
            
        logger.debug(f"[AUTH] Acceso permitido para usuario: {user.username}")
        return await call_next(request)
    except Exception as e:
        logger.error(f"[AUTH] Error de autenticación: {str(e)}")
        return RedirectResponse(url="/auth/login", status_code=303)