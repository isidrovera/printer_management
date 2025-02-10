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

    # Excluir WebSockets de la autenticación
    if request.scope["type"] == "websocket":
        return await call_next(request)

    # Permitir ciertas rutas sin autenticación
    if request.url.path.startswith(("/auth/login", "/static/", "/favicon.ico")):
        return await call_next(request)

    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)

    try:
        user = await get_current_user(request)
        request.state.user = user

        if user.must_change_password and not request.url.path.startswith("/auth/change-password"):
            return RedirectResponse(url="/auth/change-password", status_code=303)
    except Exception as e:
        logger.error(f"[AUTH] Error: {str(e)}")
        return RedirectResponse(url="/auth/login", status_code=303)

    return await call_next(request)
