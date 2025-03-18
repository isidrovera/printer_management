# server/app/middleware/first_login_middleware.py
from fastapi import Request
from fastapi.responses import RedirectResponse, Response
import logging

logger = logging.getLogger(__name__)

async def first_login_middleware(request: Request, call_next):
    logger.debug(f"[FIRST_LOGIN] Procesando ruta: {request.url.path}")

    if request.method == "OPTIONS":
        logger.debug("[FIRST_LOGIN] Solicitud OPTIONS permitida con headers explícitos")
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )

    try:
        user = getattr(request.state, "user", None)
        logger.debug(f"[FIRST_LOGIN] Usuario obtenido del state: {user.username if user else 'Ninguno'}")

        if user and user.must_change_password:
            if not request.url.path.startswith("/api/v1/auth/change-password"):
                logger.info(f"[FIRST_LOGIN] Redirigiendo usuario {user.username} a cambiar contraseña")
                return RedirectResponse(url="/auth/change-password", status_code=303)

    except Exception as e:
        logger.error(f"[FIRST_LOGIN] Error inesperado: {e}")

    return await call_next(request)
