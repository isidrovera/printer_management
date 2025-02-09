# server/app/middleware/auth_middleware.py
from fastapi import Request
from fastapi.responses import RedirectResponse
from app.core.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    """
    Middleware para verificar autenticación en rutas protegidas
    """
    # Rutas que no requieren autenticación
    public_paths = [
        "/auth/login",
        "/auth/token",
        "/static",
        "/favicon.ico"
    ]

    # Verificar si la ruta actual es pública
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    try:
        # Verificar token de autenticación
        user = await get_current_user(request, None)
        if not user:
            logger.warning(f"Intento de acceso no autorizado a: {request.url.path}")
            return RedirectResponse(url="/auth/login", status_code=303)
        
        # Si el usuario debe cambiar su contraseña, redirigir
        if user.must_change_password and not request.url.path.startswith("/auth/change-password"):
            return RedirectResponse(url="/auth/change-password", status_code=303)
        
        # Guardar el usuario en el estado de la request
        request.state.user = user
        return await call_next(request)
        
    except Exception as e:
        logger.error(f"Error en autenticación: {str(e)}")
        return RedirectResponse(url="/auth/login", status_code=303)