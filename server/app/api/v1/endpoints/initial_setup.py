# server/app/api/v1/endpoints/initial_setup.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from server.app.db.session import get_db
from server.app.services.initial_setup import InitialSetupService

router = APIRouter()

@router.post("/setup-initial-admin")
async def setup_initial_admin(db: Session = Depends(get_db)):
    """
    Endpoint para forzar creación del usuario admin inicial
    """
    created = InitialSetupService.check_and_create_initial_admin(db)
    return {
        "admin_created": created,
        "message": "Usuario admin inicial configurado" if created else "Admin ya existente"
    }