# server/app/core/auth.py
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from app.core.config import settings
from app.services.user_service import UserService
from app.db.session import get_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

def create_access_token(data: dict) -> str:
    """
    Crea un token JWT de acceso
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    return encoded_jwt

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    Obtiene el usuario actual basado en el token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Intentar obtener token de cookie primero
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token.split("Bearer ")[1]
        # Si no hay cookie, intentar obtener del header
        if not token:
            token = await oauth2_scheme(request)
            
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
    except jwt.PyJWTError:
        raise credentials_exception
        
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user = Depends(get_current_user)
):
    """
    Verifica que el usuario actual esté activo
    """
    if not current_user.is_active_user():
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user