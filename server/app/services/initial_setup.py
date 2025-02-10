# server/app/services/initial_setup.py
from sqlalchemy.orm import Session
from app.db.models.user import User, UserRole, UserDepartment, UserStatus
from app.core.config import settings
import secrets
import logging

logger = logging.getLogger(__name__)

class InitialSetupService:
    @staticmethod
    def create_initial_admin(db: Session) -> User:
        """
        Crea un usuario administrador inicial con contraseña temporal
        """
        # Verificar si ya existe un admin
        existing_admin = db.query(User).filter(
            User.role == UserRole.ADMIN, 
            User.username == "admin"
        ).first()
        
        if existing_admin:
            logger.info("Usuario admin ya existe")
            return existing_admin
        
        # Generar contraseña temporal con un formato más predecible
        temp_password = "Admin123!"
        
        # Crear usuario admin
        admin_user = User(
            username="admin",
            email="admin@empresa.local",
            full_name="Administrador Principal",
            role=UserRole.ADMIN,
            department=UserDepartment.ADMIN,
            status=UserStatus.ACTIVE,
            is_superuser=True,
            must_change_password=True,  # Forzar cambio de contraseña
            can_login=True
        )
        
        # Establecer contraseña temporal
        admin_user.set_password(temp_password)
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Imprimir por consola para mayor visibilidad
        print("\n" + "=" * 50)
        print("CREDENCIALES INICIALES DE ADMINISTRADOR:")
        print(f"Usuario: admin")
        print(f"Contraseña temporal: {temp_password}")
        print("=" * 50 + "\n")
        
        logger.info(f"Usuario admin creado con contraseña temporal")
        return admin_user

    @staticmethod
    def check_and_create_initial_admin(db: Session):
        """
        Verifica y crea el usuario admin inicial si no existe
        """
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        
        if admin_count == 0:
            InitialSetupService.create_initial_admin(db)
        
        return admin_count == 0