# server/app/api/v1/endpoints/auth.py
# server/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.user_service import UserService
from app.schemas.auth import (
    TwoFactorSetup, 
    TwoFactorVerify, 
    OAuth2Login, 
    TokenResponse, 
    RefreshTokenRequest,
    ChangePasswordRequest
)
from app.schemas.user import UserCreate, UserUpdate, UserInDB
import pyotp
import logging
from app.core.auth import create_access_token, get_current_user, get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Endpoints de autenticación de dos factores (2FA)
@router.post("/2fa/setup", response_model=dict)
async def setup_2fa(
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Configura la autenticación de dos factores y retorna el código QR"""
    user_service = UserService(db)
    secret = pyotp.random_base32()
    qr_code = user_service.generate_2fa_qr(current_user.username, secret)
    
    await user_service.update_2fa_secret(current_user.id, secret)
    
    return {
        "qr_code": qr_code,
        "secret": secret
    }

@router.post("/2fa/verify", response_model=dict)
async def verify_2fa(
    code: TwoFactorVerify,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Verifica el código 2FA y habilita 2FA para el usuario"""
    user_service = UserService(db)
    if await user_service.verify_2fa_code(current_user.id, code.code):
        return {"success": True, "message": "2FA habilitado correctamente"}
    raise HTTPException(
        status_code=400,
        detail="Código inválido"
    )

@router.post("/login", response_model=dict)
async def login(
    credentials: OAuth2Login,
    db: Session = Depends(get_db)
):
    """Endpoint de inicio de sesión"""
    try:
        user_service = UserService(db)
        user = await user_service.authenticate_user(
            credentials.username,
            credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Credenciales incorrectas"
            )
            
        access_token = create_access_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "must_change_password": user.must_change_password
            }
        }
        
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error en el servidor"
        )

@router.post("/token")
async def get_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Endpoint para obtener token de acceso"""
    try:
        user_service = UserService(db)
        user = await user_service.authenticate_user(
            form_data.username,
            form_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Credenciales incorrectas"
            )
            
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        logger.error(f"Error generando token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error en el servidor"
        )

@router.post("/logout")
async def logout():
    """Endpoint para cerrar sesión"""
    return {"message": "Sesión cerrada exitosamente"}

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Endpoint para cambiar la contraseña"""
    try:
        if password_data.new_password != password_data.confirm_password:
            raise HTTPException(
                status_code=400,
                detail="Las contraseñas no coinciden"
            )
            
        user_service = UserService(db)
        success = await user_service.change_password(
            current_user.id,
            password_data.current_password,
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Error cambiando la contraseña"
            )
        
        return {"message": "Contraseña actualizada exitosamente"}
        
    except Exception as e:
        logger.error(f"Error en cambio de contraseña: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error en el servidor"
        )