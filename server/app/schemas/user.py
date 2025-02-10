from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
import re

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    department: Optional[str] = None
    role: str = "viewer"

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

    @validator('username')
    def username_format(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', v):
            raise ValueError('Username debe tener entre 3-20 caracteres (letras, números y _)')
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str
    two_factor_code: Optional[str] = None