# app/middleware/https.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.scheme == "https" and not request.base_url.hostname == "localhost":
            https_url = str(request.url.replace(scheme="https"))
            return RedirectResponse(https_url, status_code=301)
        return await call_next(request)