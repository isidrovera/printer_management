# server/app/core/auth.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from fastapi.responses import JSONResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
import jwt
import pyotp
import qrcode
import base64
from io import BytesIO
from app.core.config import settings
from app.services.user_service import UserService
from app.db.session import get_db
from sqlalchemy.orm import Session
import logging

# Configuración de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# OAuth2 config
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Configurar OAuth providers
config = Config('.env')
oauth = OAuth(config)

# Google OAuth2
oauth.register(
   name='google',
   server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
   client_kwargs={'scope': 'openid email profile'}
)

def generate_2fa_secret() -> str:
   """Genera un secreto para 2FA"""
   return pyotp.random_base32()

def generate_2fa_qr(username: str, secret: str) -> str:
   """Genera código QR para 2FA"""
   totp = pyotp.TOTP(secret)
   provisioning_uri = totp.provisioning_uri(username, issuer_name="PrinterManagement")
   
   qr = qrcode.QRCode(version=1, box_size=10, border=5)
   qr.add_data(provisioning_uri)
   qr.make(fit=True)
   
   img = qr.make_image(fill_color="black", back_color="white")
   buffered = BytesIO()
   img.save(buffered)
   img_str = base64.b64encode(buffered.getvalue()).decode()
   
   return f"data:image/png;base64,{img_str}"

def verify_2fa_code(secret: str, code: str) -> bool:
   """Verifica código 2FA"""
   totp = pyotp.TOTP(secret)
   return totp.verify(code)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
   """
   Crea un token JWT de acceso
   
   Args:
       data: Datos a codificar en el token
       expires_delta: Tiempo de expiración opcional
       
   Returns:
       str: Token JWT codificado
   """
   try:
       to_encode = data.copy()
       if expires_delta:
           expire = datetime.utcnow() + expires_delta
       else:
           expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
           
       to_encode.update({"exp": expire, "iat": datetime.utcnow()})
       
       encoded_jwt = jwt.encode(
           to_encode,
           settings.SECRET_KEY,
           algorithm=settings.JWT_ALGORITHM
       )
       
       logger.debug(f"Token JWT creado para usuario: {data.get('sub')}")
       return encoded_jwt
       
   except Exception as e:
       logger.error(f"Error creando token JWT: {str(e)}")
       raise

def create_refresh_token(data: Dict[str, Any]) -> str:
   """Crea un token de actualización con mayor duración"""
   return create_access_token(
       data=data,
       expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
   )

def get_current_user(request: Request) -> Optional[User]:
    token = request.cookies.get("auth_token")
    if not token and "Authorization" in request.headers:
        auth = request.headers["Authorization"]
        if auth.startswith("Bearer "):
            token = auth.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return verify_token(payload)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_active_user(
   current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
   """
   Verifica que el usuario actual esté activo
   
   Args:
       current_user: Usuario actual
       
   Returns:
       Dict: Usuario verificado
       
   Raises:
       HTTPException: Si el usuario está inactivo
   """
   if not current_user.is_active_user():
       logger.warning(f"Intento de acceso de usuario inactivo: {current_user.username}")
       raise HTTPException(status_code=400, detail="Usuario inactivo")
       
   return current_user

async def authenticate_user(
   db: Session,
   username: str,
   password: str,
   code_2fa: Optional[str] = None
) -> Optional[Dict[str, Any]]:
   """
   Autentica un usuario verificando credenciales y 2FA
   
   Args:
       db: Sesión de base de datos
       username: Nombre de usuario
       password: Contraseña
       code_2fa: Código 2FA opcional
       
   Returns:
       Dict: Usuario autenticado o None
   """
   try:
       user_service = UserService(db)
       user = await user_service.get_user_by_username(username)
       
       if not user:
           logger.warning(f"Intento de login con usuario inexistente: {username}")
           return None
           
       if not user.verify_password(password):
           logger.warning(f"Contraseña incorrecta para usuario: {username}")
           await user_service.record_failed_login(user.id)
           return None
           
       # Verificar 2FA si está habilitado
       if user.two_factor_enabled:
           if not code_2fa:
               logger.warning(f"Código 2FA requerido para usuario: {username}")
               return None
               
           if not verify_2fa_code(user.two_factor_secret, code_2fa):
               logger.warning(f"Código 2FA inválido para usuario: {username}")
               return None
               
       await user_service.record_successful_login(user.id)
       logger.info(f"Login exitoso para usuario: {username}")
       return user
       
   except Exception as e:
       logger.error(f"Error en autenticación: {str(e)}")
       return None