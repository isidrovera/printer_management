# server/app/middleware/first_login_middleware.py
from fastapi import Request
from fastapi.responses import RedirectResponse
import logging

logger = logging.getLogger(__name__)

async def first_login_middleware(request: Request, call_next):
    if request.url.path.startswith(("/api/", "/monitor/")):
        user = getattr(request.state, "user", None)
        
        if user and user.must_change_password:
            if not request.url.path.startswith("/auth/change-password"):
                logger.info(f"Redirigiendo a usuario {user.username} a cambio de contraseña obligatorio")
                return RedirectResponse(url="/auth/change-password", status_code=303)
    
    response = await call_next(request)
    return response