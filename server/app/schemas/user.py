# app/schemas/user.py
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
import re
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    OPERATOR = "operator"
    VIEWER = "viewer"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class UserDepartment(str, Enum):
    IT = "it"
    OPERATIONS = "operations"
    SUPPORT = "support"
    SALES = "sales"
    ADMIN = "admin"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    department: Optional[UserDepartment] = None
    role: UserRole = UserRole.VIEWER

    @validator('username')
    def username_format(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', v):
            raise ValueError('Username debe tener entre 3-20 caracteres (letras, números y _)')
        return v

class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Contraseña debe tener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('Contraseña debe tener al menos una minúscula')
        if not re.search(r'\d', v):
            raise ValueError('Contraseña debe tener al menos un número')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Contraseña debe tener al menos un carácter especial')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None 
    full_name: Optional[str] = None
    department: Optional[UserDepartment] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    password: Optional[str] = None

    @validator('password')
    def password_strength(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Contraseña debe tener al menos 8 caracteres')
            if not re.search(r'[A-Z]', v):
                raise ValueError('Contraseña debe tener al menos una mayúscula')
            if not re.search(r'[a-z]', v):
                raise ValueError('Contraseña debe tener al menos una minúscula') 
            if not re.search(r'\d', v):
                raise ValueError('Contraseña debe tener al menos un número')
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
                raise ValueError('Contraseña debe tener al menos un carácter especial')
        return v

class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    must_change_password: bool = False
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserBase):
    id: int
    role: UserRole
    status: UserStatus
    department: Optional[UserDepartment]
    job_title: Optional[str]
    phone: Optional[str]
    mobile: Optional[str]
    is_superuser: bool
    can_login: bool
    email_verified: bool
    must_change_password: bool = False
    failed_login_attempts: int = 0
    last_login: Optional[datetime]
    last_active: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Contraseña debe tener al menos una mayúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('Contraseña debe tener al menos una minúscula')
        if not re.search(r'\d', v):
            raise ValueError('Contraseña debe tener al menos un número')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Contraseña debe tener al menos un carácter especial')
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Las contraseñas no coinciden')
        return v