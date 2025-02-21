# server/app/services/user_service.py
from sqlalchemy.orm import Session
from app.db.models.user import User, Permission, UserStatus
from app.schemas.user import UserCreate, UserUpdate, UserInDB
from fastapi import HTTPException
import logging
from typing import Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db: Session):
        self.db = db

    async def create_user(self, user_data: UserCreate, created_by_id: Optional[int] = None) -> User:
        """Crea un nuevo usuario."""
        try:
            logger.info(f"Iniciando creación de usuario: {user_data.username}")
            
            # Verificar si el usuario ya existe
            if self.db.query(User).filter(User.username == user_data.username).first():
                logger.warning(f"Intento de crear usuario con username duplicado: {user_data.username}")
                raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
            
            if self.db.query(User).filter(User.email == user_data.email).first():
                logger.warning(f"Intento de crear usuario con email duplicado: {user_data.email}")
                raise HTTPException(status_code=400, detail="El email ya está registrado")
            
            # Crear el usuario
            user = User(
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                role=user_data.role,
                department=user_data.department,
                status=UserStatus.ACTIVE,
                created_by_id=created_by_id,
                must_change_password=True  # Forzar cambio de contraseña en primer login
            )
            
            # Establecer la contraseña
            user.set_password(user_data.password)
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Usuario creado exitosamente: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Error creando usuario: {str(e)}")
            self.db.rollback()
            raise

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por su ID."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"Usuario no encontrado con ID: {user_id}")
                return None
            return user
        except Exception as e:
            logger.error(f"Error obteniendo usuario por ID: {str(e)}")
            raise

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por su nombre de usuario."""
        try:
            return self.db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Error obteniendo usuario por username: {str(e)}")
            raise

    async def update_user(self, user_id: int, user_data: UserUpdate, updated_by_id: Optional[int] = None) -> Optional[User]:
        """Actualiza un usuario existente."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return None

            # Actualizar campos
            for field, value in user_data.dict(exclude_unset=True).items():
                setattr(user, field, value)

            user.updated_by_id = updated_by_id
            user.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Usuario actualizado exitosamente: {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"Error actualizando usuario: {str(e)}")
            self.db.rollback()
            raise

    async def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Cambia la contraseña de un usuario."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False

            # Verificar contraseña actual
            if not user.verify_password(current_password):
                logger.warning(f"Intento de cambio de contraseña con contraseña actual incorrecta: {user.username}")
                raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

            # Cambiar contraseña
            user.set_password(new_password)
            user.must_change_password = False
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Contraseña cambiada exitosamente para usuario: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error cambiando contraseña: {str(e)}")
            self.db.rollback()
            raise

    async def deactivate_user(self, user_id: int) -> bool:
        """Desactiva un usuario."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False

            user.status = UserStatus.INACTIVE
            user.can_login = False
            user.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Usuario desactivado: {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"Error desactivando usuario: {str(e)}")
            self.db.rollback()
            raise

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Obtiene lista de usuarios con paginación."""
        try:
            return self.db.query(User).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error obteniendo lista de usuarios: {str(e)}")
            raise

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Autentica un usuario por username y contraseña."""
        try:
            user = await self.get_user_by_username(username)  # 🔹 Corregido: ahora usa `await`
            if not user:
                logger.warning(f"Usuario no encontrado: {username}")
                return None
            
            if not user.is_active_user():  # Asegurar que el usuario no está inactivo
                logger.warning(f"Intento de login de usuario inactivo: {username}")
                return None
                
            if not user.verify_password(password):
                logger.warning(f"Contraseña incorrecta para usuario: {username}")
                return None

            # Si la contraseña es correcta, resetear intentos fallidos
            user.failed_login_attempts = 0
            user.last_login = datetime.utcnow()
            user.last_login_attempt = None
            user.locked_until = None

            self.db.commit()
            return user

        except Exception as e:
            logger.error(f"Error en autenticación: {str(e)}")
            raise
