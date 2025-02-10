# server/app/middleware/auth_middleware.py
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
import logging
from app.core.auth import get_current_user
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    logger.debug(f"Procesando solicitud para ruta: {request.url.path}")
    
    public_paths = ["/auth/login", "/static/", "/favicon.ico"]
    if any(request.url.path.startswith(path) for path in public_paths):
        logger.debug(f"Acceso a ruta pública permitido: {request.url.path}")
        return await call_next(request)

    token = request.cookies.get("auth_token")
    
    if not token:
        logger.error("Token no encontrado en cookies")
        if not request.url.path.startswith("/auth/"):
            logger.info("Redirigiendo a login por falta de token")
            return RedirectResponse(url="/auth/login", status_code=303)
    
    if token:
        try:
            db = SessionLocal()
            user = await get_current_user(request)
            
            if user and user.must_change_password:
                if not request.url.path.startswith("/auth/change-password"):
                    logger.info(f"Usuario {user.username} debe cambiar contraseña, redirigiendo")
                    return RedirectResponse(url="/auth/change-password", status_code=303)
            
            request.state.user = user
            logger.debug(f"Usuario autenticado: {user.username}")
        except Exception as e:
            logger.error(f"Error verificando usuario: {str(e)}")
            return RedirectResponse(url="/auth/login", status_code=303)
        finally:
            db.close()

    response = await call_next(request)
    return response