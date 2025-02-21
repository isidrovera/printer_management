# server/app/api/v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.user_service import UserService
from app.schemas.auth import (TwoFactorSetup, TwoFactorVerify, OAuth2Login, TokenResponse, RefreshTokenRequest)
from app.schemas.user import UserCreate, UserUpdate, UserInDB
import pyotp
import json
from app.core.auth import create_access_token, get_current_user, get_current_active_user
from fastapi.templating import Jinja2Templates
from typing import Optional
import logging
from fastapi import Form, Response
logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
# Nuevos endpoints de 2FA


@router.post("/api-login")
async def api_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Endpoint específico para login desde React"""
    try:
        user_service = UserService(db)
        user = await user_service.authenticate_user(username, password)
        
        if not user:
            return JSONResponse(
                status_code=401,
                content={"detail": "Credenciales incorrectas"}
            )
            
        # En lugar de redireccionar, devolver directamente el token y la data
        access_token = create_access_token(data={"sub": user.username})
        
        return JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "username": user.username,
                    "must_change_password": user.must_change_password
                }
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error en login API: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )
@router.post("/2fa/setup")
async def setup_2fa(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Configura autenticación de dos factores"""
    user_service = UserService(db)
    secret = pyotp.random_base32()
    qr_code = user_service.generate_2fa_qr(current_user.username, secret)
    
    await user_service.update_2fa_secret(current_user.id, secret)
    
    return templates.TemplateResponse(
        "auth/2fa_setup.html",
        {
            "request": request,
            "qr_code": qr_code,
            "secret": secret
        }
    )

@router.post("/2fa/verify")
async def verify_2fa(
    request: Request,
    code: TwoFactorVerify,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Verifica código 2FA y habilita 2FA"""
    user_service = UserService(db)
    if await user_service.verify_2fa_code(current_user.id, code.code):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        "auth/2fa_verify.html",
        {
            "request": request,
            "error": "Código inválido"
        }
    )
# Rutas de API
@router.post("/token")
async def login_for_access_token(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Endpoint para obtener token de acceso vía API"""
    try:
        user_service = UserService(db)
        user = await user_service.authenticate_user(username, password)
        
        if not user:
            return JSONResponse(
                status_code=401,
                content={"detail": "Credenciales incorrectas"}
            )
            
        # Si es una petición de la web UI, manejala con redirección
        if "text/html" in request.headers.get("accept", ""):
            access_token = create_access_token(data={"sub": user.username})
            response = RedirectResponse(
                url="/auth/change-password" if user.must_change_password else "/",
                status_code=303
            )
            response.set_cookie(
                key="access_token",
                value=f"Bearer {access_token}",
                httponly=True
            )
            return response
            
        # Si es una petición de API, devuelve JSON
        access_token = create_access_token(data={"sub": user.username})
        return JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "username": user.username,
                    "must_change_password": user.must_change_password
                }
            },
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Error en el servidor"}
        )
# Rutas Web
@router.get("/login")
async def login_form(request: Request):
    """Muestra el formulario de login"""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request}
    )

@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    try:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        user_service = UserService(db)
        user = await user_service.authenticate_user(username, password)
        
        if not user:
            return templates.TemplateResponse(
                "auth/login.html",
                {"request": request, "error": "Credenciales incorrectas"}
            )
            
        access_token = create_access_token(data={"sub": user.username})
        response = RedirectResponse(url="/auth/change-password" if user.must_change_password else "/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True
        )
        
        logger.info(f"Login exitoso: {username}")
        return response
        
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Error en el servidor"}
        )

@router.get("/logout")
async def logout():
    """Cierra la sesión del usuario"""
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("access_token")
    return response

@router.get("/change-password")
async def change_password_form(
    request: Request,
    current_user: UserInDB = Depends(get_current_user)
):
    """Muestra el formulario de cambio de contraseña"""
    return templates.TemplateResponse(
        "auth/change_password.html",
        {
            "request": request,
            "user": current_user,
            "force_change": current_user.must_change_password
        }
    )

@router.post("/change-password")
async def change_password(
    request: Request,
    db: Session = Depends(get_db),
    current_user: UserInDB = Depends(get_current_user)
):
    """Procesa el cambio de contraseña"""
    try:
        form = await request.form()
        current_password = form.get("current_password")
        new_password = form.get("new_password")
        confirm_password = form.get("confirm_password")
        
        if new_password != confirm_password:
            raise ValueError("Las contraseñas no coinciden")
            
        user_service = UserService(db)
        success = await user_service.change_password(
            current_user.id,
            current_password,
            new_password
        )
        
        if not success:
            raise ValueError("Error cambiando la contraseña")
        
        return RedirectResponse(url="/", status_code=303)
        
    except ValueError as e:
        return templates.TemplateResponse(
            "auth/change_password.html",
            {
                "request": request,
                "user": current_user,
                "error": str(e),
                "force_change": current_user.must_change_password
            }
        )
    except Exception as e:
        logger.error(f"Error en cambio de contraseña: {str(e)}")
        return templates.TemplateResponse(
            "auth/change_password.html",
            {
                "request": request,
                "user": current_user,
                "error": "Error en el servidor",
                "force_change": current_user.must_change_password
            }
        )