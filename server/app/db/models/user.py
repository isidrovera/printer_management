# server/app/db/models/user.py
from app.db.base import BaseModel
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum, Integer, TIMESTAMP, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    OPERATOR = "operator"
    VIEWER = "viewer"

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class UserDepartment(str, enum.Enum):
    IT = "it"
    OPERATIONS = "operations"
    SUPPORT = "support"
    SALES = "sales"
    ADMIN = "admin"

# Tabla de asociación para permisos de usuario
user_permissions = Table(
    'user_permissions',
    BaseModel.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)

class User(BaseModel):
    __tablename__ = 'users'
    
    # Información básica
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Información de perfil
    profile_picture = Column(String(255))
    job_title = Column(String(100))
    department = Column(Enum(UserDepartment))
    employee_id = Column(String(50), unique=True)
    phone = Column(String(20))
    mobile = Column(String(20))
    
    # Roles y permisos
    role = Column(Enum(UserRole), default=UserRole.VIEWER)
    is_superuser = Column(Boolean, default=False)
    can_login = Column(Boolean, default=True)
    
    # Configuración de cuenta
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    email_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(32))
    two_factor_backup_codes = Column(Text) 
    must_change_password = Column(Boolean, default=False)
    
    # Control de acceso
    failed_login_attempts = Column(Integer, default=0)
    last_login_attempt = Column(TIMESTAMP)
    locked_until = Column(TIMESTAMP)
    last_login = Column(TIMESTAMP)
    last_active = Column(TIMESTAMP)
    auth_token = Column(String(255), unique=True)
    oauth_provider = Column(String(20))
    oauth_id = Column(String(100))
    refresh_token = Column(String(255))
    refresh_token_expires_at = Column(TIMESTAMP)
    
    # Auditoría
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey('users.id'))
    updated_by_id = Column(Integer, ForeignKey('users.id'))
    
    # Relaciones
    permissions = relationship("Permission", secondary=user_permissions, back_populates="users")
    created_by = relationship("User", backref="created_users", remote_side=[id], foreign_keys=[created_by_id])
    updated_by = relationship("User", backref="updated_users", remote_side=[id], foreign_keys=[updated_by_id])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.auth_token:
            self.auth_token = self.generate_auth_token()
            
    @staticmethod
    def generate_auth_token():
        return f"usr_{uuid.uuid4().hex}"
    
    def set_password(self, password: str):
        """Establece la contraseña hasheada del usuario"""
        self.hashed_password = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verifica si la contraseña proporcionada es correcta"""
        return pwd_context.verify(password, self.hashed_password)
    
    def is_active_user(self) -> bool:
        """Verifica si el usuario está activo"""
        return (
            self.status == UserStatus.ACTIVE and
            self.can_login and
            (not self.locked_until or self.locked_until < datetime.utcnow())
        )
    
    def to_dict(self):
        """Convierte el objeto a diccionario para serialización"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value if self.role else None,
            "department": self.department.value if self.department else None,
            "status": self.status.value if self.status else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Permission(BaseModel):
    __tablename__ = 'permissions'
    
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    users = relationship("User", secondary=user_permissions, back_populates="permissions")