# server/app/middleware/auth_middleware.py
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
import logging

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    # Permitir acceso a rutas públicas
    public_paths = ["/auth/login", "/static/", "/favicon.ico"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    # Verificar autenticación para otras rutas
    if "auth_token" not in request.cookies:
        logger.error("Token no encontrado en cookies")
        return RedirectResponse(url="/auth/login", status_code=303)

    response = await call_next(request)
    return response