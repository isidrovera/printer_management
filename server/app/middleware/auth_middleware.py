# server/app/middleware/auth_middleware.py
from fastapi import Request
from fastapi.responses import RedirectResponse
import logging
from app.core.auth import get_current_user
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    logger.debug(f"Procesando solicitud: {request.url.path}")
    
    # Rutas públicas
    public_paths = ["/auth/login", "/static/", "/favicon.ico"]
    if any(request.url.path.startswith(path) for path in public_paths):
        logger.debug(f"Acceso permitido a ruta pública: {request.url.path}")
        return await call_next(request)

    # Verificar token
    token = request.cookies.get("access_token")  # Cambiado de auth_token a access_token
    
    if not token:
        logger.error("Token no encontrado en cookies")
        return RedirectResponse(url="/auth/login", status_code=303)

    try:
        db = SessionLocal()
        try:
            # Verificar usuario
            user = await get_current_user(request)
            request.state.user = user
            logger.debug(f"Usuario autenticado: {user.username}")

            # Redirigir a cambio de contraseña si es necesario
            if user.must_change_password and not request.url.path.startswith("/auth/change-password"):
                logger.info(f"Redirigiendo a cambio de contraseña: {user.username}")
                return RedirectResponse(url="/auth/change-password", status_code=303)

        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error de autenticación: {str(e)}")
        return RedirectResponse(url="/auth/login", status_code=303)

    return await call_next(request)