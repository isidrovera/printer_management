# server/app/schemas/auth.py
# server/app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class OAuthProvider(str, Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LoginRequest(BaseModel):
    username: str
    password: str
    code_2fa: Optional[str] = None

class OAuth2Login(BaseModel):
    provider: OAuthProvider
    code: str
    redirect_uri: str

class TwoFactorSetup(BaseModel):
    secret: str
    qr_code: str

class TwoFactorVerify(BaseModel):
    code: str

class TwoFactorDisable(BaseModel):
    password: str
    code: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetVerify(BaseModel):
    token: str
    new_password: str

class LoginResponse(BaseModel):
    user_id: int
    username: str
    token: TokenResponse
    requires_2fa: bool = False
    two_factor_enabled: bool = False

# Nuevo esquema para cambio de contraseña
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

# Nuevo esquema para la respuesta detallada del usuario al iniciar sesión
class UserLoginResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    role: str
    must_change_password: bool
    access_token: str
    token_type: str = "bearer"

# Nuevo esquema para respuestas genéricas
class MessageResponse(BaseModel):
    message: str
    success: bool = True