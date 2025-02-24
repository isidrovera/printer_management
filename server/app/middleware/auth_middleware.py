# server/app/middleware/auth_middleware.py
# server/app/middleware/auth_middleware.py
from fastapi import Request
from fastapi.responses import JSONResponse
import logging
import jwt
from app.core.config import settings

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    logger.debug(f"[AUTH] Iniciando middleware para ruta: {request.url.path}")

    # Lista de rutas públicas que no requieren autenticación
    public_paths = [
        "/api/v1/auth/login",
        "/api/v1/auth/token",
        "/api/v1/auth/refresh",  # Añadir ruta para refresh token
        "/api/v1/ws/agent",
        "/api/v1/monitor/printers",
        "/api/v1/printer-oids",
        "/api/v1/agents/register",
        "/api/v1/monitor/printers/update",
        "/api/v1/agents/drivers/download",
        "/api/v1/drivers/download",
        "/api/v1/auth/refresh",
        "/favicon.ico",
        "/static",
        "/docs",  # Para Swagger UI
        "/openapi.json"  # Para la especificación OpenAPI
    ]

    # Verificar si la ruta es pública
    if any(request.url.path.startswith(path) for path in public_paths):
        logger.debug(f"[AUTH] Ruta pública permitida: {request.url.path}")
        return await call_next(request)

    try:
        # Obtener y validar el token del header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(f"[AUTH] Token no proporcionado o formato inválido: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Token de autenticación no proporcionado o inválido"}
            )

        token = auth_header.split(" ")[1]
        
        try:
            # Decodificar el token
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Añadir el usuario al scope de la petición para usarlo en los endpoints
            request.state.user = payload
            
        except jwt.ExpiredSignatureError:
            logger.error("Token expirado")
            return JSONResponse(
                status_code=401,
                content={"detail": "Token expirado"}
            )
        except jwt.InvalidTokenError:
            logger.error("Token inválido")
            return JSONResponse(
                status_code=401,
                content={"detail": "Token inválido"}
            )
            
        # Continuar con la petición
        return await call_next(request)
        
    except Exception as e:
        logger.error(f"[AUTH] Error inesperado: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error interno del servidor: {str(e)}"}
        )