# server/app/middleware/auth_middleware.py
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
import logging

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith(("/api/", "/monitor/")):
        if "auth_token" not in request.cookies:
            logger.error("Token no encontrado en cookies")
            if not request.url.path.startswith("/auth/"):
                logger.error("Error en autenticación: 401: Credenciales inválidas")
                return RedirectResponse(url="/auth/login", status_code=303)
    
    response = await call_next(request)
    return response