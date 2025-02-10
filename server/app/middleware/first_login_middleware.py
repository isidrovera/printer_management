# server/app/middleware/first_login_middleware.py
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse

async def first_login_middleware(request: Request, call_next):
    """
    Middleware para forzar cambio de contraseña en primer inicio de sesión
    """
    response = await call_next(request)
    
    # Verificar si hay un usuario logueado
    user = getattr(request.state, 'user', None)
    
    if user and user.must_change_password:
        # Redirigir a cambio de contraseña si es necesario
        if not request.url.path.startswith("/auth/change-password"):
            return RedirectResponse(url="/auth/change-password", status_code=303)
    
    return response
