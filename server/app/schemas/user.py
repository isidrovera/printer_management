# server/app/schemas/user.py
from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List
from datetime import datetime
from app.db.models.user import UserRole, UserStatus, UserDepartment

class UserBase(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50)
    full_name: constr(min_length=1, max_length=100)
    
class UserCreate(UserBase):
    password: constr(min_length=8)
    role: Optional[UserRole] = UserRole.VIEWER
    department: Optional[UserDepartment] = None
    
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[UserDepartment] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: constr(min_length=8)
    confirm_password: str

class UserInDB(UserBase):
    id: int
    role: UserRole
    status: UserStatus
    department: Optional[UserDepartment]
    is_superuser: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int
    
    class Config:
        from_attributes = True