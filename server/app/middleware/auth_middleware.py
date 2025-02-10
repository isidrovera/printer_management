# server/app/middleware/auth_middleware.py
from fastapi import Request
from fastapi.responses import RedirectResponse
import logging
from app.core.auth import get_current_user
from app.db.models.user import User
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> User:
    logger.debug("[AUTH] Iniciando verificación de usuario")
    token = request.cookies.get("access_token")
    
    if not token:
        logger.error("[AUTH] Token no encontrado")
        raise HTTPException(status_code=401)

    try:
        token = token.replace("Bearer ", "")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username = payload.get("sub")
        logger.debug(f"[AUTH] Token decodificado para usuario: {username}")

        if not username:
            logger.error("[AUTH] Username no encontrado en token")
            raise HTTPException(status_code=401)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.error(f"[AUTH] Usuario no encontrado: {username}")
                raise HTTPException(status_code=401)
            logger.info(f"[AUTH] Usuario verificado: {username}")
            return user
        finally:
            db.close()
    except JWTError as e:
        logger.error(f"[AUTH] Error JWT: {e}")
        raise HTTPException(status_code=401)