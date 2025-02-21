# server/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.user_service import UserService
from app.schemas.auth import TwoFactorVerify, TokenResponse
from app.schemas.user import UserInDB
from app.core.auth import create_access_token, get_current_user
import pyotp
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Endpoint de login que retorna token JWT y datos del usuario"""
    try:
        user_service = UserService(db)
        user = await user_service.authenticate_user(form_data.username, form_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
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
                "must_change_password": user.must_change_password,
                "has_2fa": user.has_2fa
            }
        }
        
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(status_code=500, detail="Error en el servidor")

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Endpoint para cambiar contraseña"""
    try:
        user_service = UserService(db)
        success = await user_service.change_password(
            current_user.id,
            current_password,
            new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Error cambiando la contraseña"
            )
            
        return {"message": "Contraseña actualizada exitosamente"}
        
    except Exception as e:
        logger.error(f"Error cambiando contraseña: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/2fa/setup")
async def setup_2fa(db: Session = Depends(get_db), current_user: UserInDB = Depends(get_current_user)):
    """Configura autenticación de dos factores"""
    try:
        user_service = UserService(db)
        secret = pyotp.random_base32()
        qr_code = user_service.generate_2fa_qr(current_user.username, secret)
        
        await user_service.update_2fa_secret(current_user.id, secret)
        
        return {
            "secret": secret,
            "qr_code": qr_code
        }
    except Exception as e:
        logger.error(f"Error configurando 2FA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/2fa/verify")
async def verify_2fa(
    code: TwoFactorVerify,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Verifica código 2FA"""
    try:
        user_service = UserService(db)
        if await user_service.verify_2fa_code(current_user.id, code.code):
            return {"message": "Código verificado exitosamente"}
        raise HTTPException(status_code=400, detail="Código inválido")
    except Exception as e:
        logger.error(f"Error verificando 2FA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))