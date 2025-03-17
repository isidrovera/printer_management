# server/app/api/v1/endpoints/clients.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from server.app.db.session import get_db
from server.app.services.client_service import ClientService
from server.app.schemas.client import (
    ClientCreate, 
    ClientUpdate, 
    ClientResponse, 
    ClientSearch,
    ClientDashboardStats
)
from server.app.db.models import ClientStatus, ClientType
from server.app.core.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[ClientResponse])
async def get_all_clients(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Obtiene todos los clientes"""
    try:
        client_service = ClientService(db)
        clients = await client_service.get_all()
        return clients
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo clientes: {str(e)}"
        )

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Obtiene un cliente por su ID"""
    try:
        client_service = ClientService(db)
        client = await client_service.get_by_id(client_id)
        if not client:
            raise HTTPException(
                status_code=404,
                detail="Cliente no encontrado"
            )
        return client
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo cliente: {str(e)}"
        )

@router.post("/", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Crea un nuevo cliente"""
    try:
        client_service = ClientService(db)
        client = await client_service.create(client_data.dict())
        return client
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creando cliente: {str(e)}"
        )

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Actualiza un cliente existente"""
    try:
        client_service = ClientService(db)
        updated_client = await client_service.update(client_id, client_data.dict(exclude_unset=True))
        if not updated_client:
            raise HTTPException(
                status_code=404,
                detail="Cliente no encontrado"
            )
        return updated_client
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error actualizando cliente: {str(e)}"
        )

@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Elimina un cliente"""
    try:
        client_service = ClientService(db)
        success = await client_service.delete(client_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Cliente no encontrado"
            )
        return {"message": "Cliente eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando cliente: {str(e)}"
        )

@router.get("/search/{search_term}", response_model=List[ClientResponse])
async def search_clients(
    search_term: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Busca clientes por término de búsqueda"""
    try:
        client_service = ClientService(db)
        clients = await client_service.search_clients(search_term)
        return clients
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error buscando clientes: {str(e)}"
        )

@router.get("/status/{status}", response_model=List[ClientResponse])
async def get_clients_by_status(
    status: ClientStatus,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Obtiene clientes por estado"""
    try:
        client_service = ClientService(db)
        clients = await client_service.get_by_status(status)
        return clients
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo clientes por estado: {str(e)}"
        )

@router.get("/service-level/{service_level}", response_model=List[ClientResponse])
async def get_clients_by_service_level(
    service_level: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Obtiene clientes por nivel de servicio"""
    try:
        client_service = ClientService(db)
        clients = await client_service.get_by_service_level(service_level)
        return clients
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo clientes por nivel de servicio: {str(e)}"
        )

@router.get("/manager/{account_manager}", response_model=List[ClientResponse])
async def get_clients_by_manager(
    account_manager: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Obtiene clientes por ejecutivo de cuenta"""
    try:
        client_service = ClientService(db)
        clients = await client_service.get_clients_by_account_manager(account_manager)
        return clients
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo clientes por ejecutivo: {str(e)}"
        )

@router.get("/dashboard/stats", response_model=ClientDashboardStats)
async def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Obtiene estadísticas para el dashboard"""
    try:
        client_service = ClientService(db)
        stats = await client_service.get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )