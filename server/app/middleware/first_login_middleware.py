# server/app/middleware/first_login_middleware.py
from fastapi import Request
from fastapi.responses import RedirectResponse, Response
import logging

logger = logging.getLogger(__name__)

async def first_login_middleware(request: Request, call_next):
    logger.debug(f"[FIRST_LOGIN] Inicio procesamiento: {request.url.path}")

    # 👇 Permite siempre peticiones OPTIONS para solucionar CORS
    if request.method == "OPTIONS":
        logger.debug("[FIRST_LOGIN] Solicitud OPTIONS permitida automáticamente")
        return Response(status_code=200)

    try:
        user = getattr(request.state, "user", None)
        logger.debug(f"[FIRST_LOGIN] Usuario en state: {user.username if user else None}")

        if user and user.must_change_password:
            logger.info(f"[FIRST_LOGIN] Usuario {user.username} debe cambiar contraseña")
            if not request.url.path.startswith("/api/v1/auth/change-password"):
                logger.info("[FIRST_LOGIN] Redirigiendo a cambio de contraseña")
                return RedirectResponse(url="/auth/change-password", status_code=303)
    except Exception as e:
        logger.error(f"[FIRST_LOGIN] Error: {str(e)}")

    logger.debug("[FIRST_LOGIN] Procesamiento completado")
    return await call_next(request)
