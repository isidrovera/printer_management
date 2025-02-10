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

# En el main.py o archivo de configuración de la aplicación
from fastapi import FastAPI
from app.middleware.first_login_middleware import first_login_middleware
from app.services.initial_setup import InitialSetupService

def setup_application():
    app = FastAPI()
    
    # Middleware
    app.middleware("http")(first_login_middleware)
    
    # Crear admin inicial al iniciar la aplicación
    @app.on_event("startup")
    def startup_event():
        db = next(get_db())
        InitialSetupService.check_and_create_initial_admin(db)
    
    return app