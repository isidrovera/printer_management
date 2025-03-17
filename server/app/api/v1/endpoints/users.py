# server/app/api/v1/endpoints/users.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from server.app.db.session import get_db
from server.app.services.user_service import UserService
from server.app.schemas.user import UserCreate, UserUpdate, User
from server.app.core.auth import get_current_user

router = APIRouter()

# Dependency para obtener el servicio de usuarios
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

@router.get("/", response_model=List[User])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la lista de usuarios con paginación.
    Solo accesible para usuarios autenticados.
    """
    return await user_service.get_all_users(skip=skip, limit=limit)

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    """
    Crea un nuevo usuario.
    Solo accesible para administradores.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear usuarios"
        )
    return await user_service.create_user(user_data, created_by_id=current_user.id)

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene un usuario específico por ID.
    Los usuarios solo pueden ver sus propios datos a menos que sean administradores.
    """
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver este usuario"
        )
    
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza un usuario existente.
    Los usuarios solo pueden actualizar sus propios datos a menos que sean administradores.
    """
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar este usuario"
        )
    
    user = await user_service.update_user(user_id, user_data, updated_by_id=current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return user

@router.post("/{user_id}/change-password", response_model=bool)
async def change_user_password(
    user_id: int,
    current_password: str,
    new_password: str,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    """
    Cambia la contraseña de un usuario.
    Los usuarios solo pueden cambiar su propia contraseña.
    """
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede cambiar la contraseña de otro usuario"
        )
    
    success = await user_service.change_password(user_id, current_password, new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al cambiar la contraseña"
        )
    return True

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    """
    Desactiva un usuario (soft delete).
    Solo accesible para administradores.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar usuarios"
        )
    
    success = await user_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )