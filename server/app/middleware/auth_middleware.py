# server/app/middleware/auth_middleware.py
from fastapi import Request
from fastapi.responses import RedirectResponse
import logging
from app.core.auth import get_current_user
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    logger.debug(f"[AUTH] Inicio procesamiento: {request.url.path}")
    
    public_paths = ["/auth/login", "/static/", "/favicon.ico"]
    if any(request.url.path.startswith(path) for path in public_paths):
        logger.debug(f"[AUTH] Permitiendo acceso a ruta pública: {request.url.path}")
        return await call_next(request)

    token = request.cookies.get("access_token")
    logger.debug(f"[AUTH] Token encontrado en cookies: {bool(token)}")
    
    if not token:
        logger.error("[AUTH] No hay token, redirigiendo a login")
        return RedirectResponse(url="/auth/login", status_code=303)

    try:
        db = SessionLocal()
        try:
            logger.debug("[AUTH] Verificando usuario")
            user = await get_current_user(request)
            request.state.user = user
            logger.info(f"[AUTH] Usuario autenticado: {user.username}")

            if user.must_change_password:
                logger.info(f"[AUTH] Usuario debe cambiar contraseña: {user.username}")
                if not request.url.path.startswith("/auth/change-password"):
                    logger.info("[AUTH] Redirigiendo a cambio de contraseña")
                    return RedirectResponse(url="/auth/change-password", status_code=303)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[AUTH] Error autenticando: {str(e)}")
        return RedirectResponse(url="/auth/login", status_code=303)

    logger.debug("[AUTH] Procesamiento completado")
    return await call_next(request)