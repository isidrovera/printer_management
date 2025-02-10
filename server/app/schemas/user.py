# app/schemas/user.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
import re
from datetime import datetime

class UserBase(BaseModel):
   username: str
   email: EmailStr
   full_name: str
   department: Optional[str] = None
   role: str = "viewer"

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
   department: Optional[str] = None
   role: Optional[str] = None
   password: Optional[str] = None

   @validator('password')
   def password_strength(cls, v):
       if v is not None:
           # Same password validation as UserCreate
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