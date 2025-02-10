# server/app/middleware/auth_middleware.py
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
import logging

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    public_paths = ["/auth/login", "/static/", "/favicon.ico", "/auth/change-password"]
    
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)

    token = request.cookies.get("auth_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=303)

    if token and request.url.path == "/auth/login":
        return RedirectResponse(url="/auth/change-password", status_code=303)

    return await call_next(request)