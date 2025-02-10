# server/app/services/initial_setup.py
from sqlalchemy.orm import Session
from app.db.models.user import User, UserRole, UserDepartment, UserStatus, Permission
from app.schemas.user import UserCreate
from datetime import datetime, timedelta
import logging
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

class InitialSetupService:
    @staticmethod
    def create_initial_admin(db: Session) -> Tuple[User, str]:
        try:
            existing_admin = db.query(User).filter(User.username == "admin").first()
            if existing_admin:
                return existing_admin, None

            temp_password = "Admin123!"
            admin_user = User(
                username="admin",
                email="admin@empresa.local",
                full_name="Administrador Principal",
                role=UserRole.ADMIN,
                department=UserDepartment.ADMIN,
                status=UserStatus.ACTIVE,
                is_superuser=True,
                can_login=True,
                must_change_password=True,
                failed_login_attempts=0,
                email_verified=True,
                two_factor_enabled=False,
                auth_token=User.generate_auth_token(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            admin_user.set_password(temp_password)
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            print("\n" + "=" * 50)
            print("CREDENCIALES INICIALES:")
            print(f"Usuario: admin")
            print(f"Contraseña: {temp_password}")
            print("=" * 50 + "\n")
            
            return admin_user, temp_password

        except Exception as e:
            logger.error(f"Error en create_initial_admin: {e}")
            db.rollback()
            raise

    @staticmethod
    async def setup_initial_permissions(db: Session):
        try:
            permissions = [
                ("user_manage", "Gestión de usuarios"),
                ("printer_manage", "Gestión de impresoras"),
                ("job_manage", "Gestión de trabajos"),
                ("report_view", "Visualización de reportes"),
                ("system_config", "Configuración del sistema")
            ]
            
            for name, description in permissions:
                if not db.query(Permission).filter(Permission.name == name).first():
                    db.add(Permission(name=name, description=description))
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error en setup_initial_permissions: {e}")
            db.rollback()
            raise

    @staticmethod
    async def assign_admin_permissions(db: Session, admin_user: User):
        try:
            permissions = db.query(Permission).all()
            admin_user.permissions.extend(permissions)
            db.commit()
        except Exception as e:
            logger.error(f"Error en assign_admin_permissions: {e}")
            db.rollback()
            raise

    @staticmethod
    async def run_initial_setup(db: Session) -> Dict[str, Any]:
        try:
            admin_user, password = InitialSetupService.create_initial_admin(db)
            await InitialSetupService.setup_initial_permissions(db)
            await InitialSetupService.assign_admin_permissions(db, admin_user)
            
            return {
                "success": True,
                "admin_created": password is not None,
                "message": "Configuración inicial completada"
            }
        except Exception as e:
            logger.error(f"Error en run_initial_setup: {e}")
            return {"success": False, "error": str(e)}