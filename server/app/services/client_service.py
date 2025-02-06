# app/services/client_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..db.models import Client, ClientType, ClientStatus
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ClientService:
    def __init__(self, db: Session):
        self.db = db

    async def get_all(self) -> List[Client]:
        """Obtiene todos los clientes."""
        return self.db.query(Client).all()

    async def get_by_id(self, client_id: int) -> Optional[Client]:
        """Obtiene un cliente por su ID."""
        return self.db.query(Client).filter(Client.id == client_id).first()

    async def search_clients(self, search_term: str) -> List[Client]:
        """Busca clientes por varios criterios."""
        return self.db.query(Client).filter(
            or_(
                Client.name.ilike(f"%{search_term}%"),
                Client.business_name.ilike(f"%{search_term}%"),
                Client.tax_id.ilike(f"%{search_term}%"),
                Client.client_code.ilike(f"%{search_term}%"),
                Client.contact_email.ilike(f"%{search_term}%")
            )
        ).all()

    async def create(self, client_data: Dict[str, Any]) -> Client:
        """
        Crea un nuevo cliente con todos sus datos.
        
        Args:
            client_data: Diccionario con todos los datos del cliente
        """
        try:
            # Procesamiento de datos enum
            if 'client_type' in client_data:
                client_data['client_type'] = ClientType(client_data['client_type'])
            if 'status' in client_data:
                client_data['status'] = ClientStatus(client_data['status'])

            # Procesamiento de fechas
            date_fields = ['contract_start_date', 'contract_end_date', 'last_contact_date']
            for field in date_fields:
                if field in client_data and client_data[field]:
                    client_data[field] = datetime.fromisoformat(client_data[field])

            # Crear el cliente con todos los campos
            client = Client(
                token=Client.generate_token(),
                **client_data
            )
            
            self.db.add(client)
            self.db.commit()
            self.db.refresh(client)
            
            logger.info(f"Cliente creado exitosamente: {client.name} (ID: {client.id})")
            return client
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando cliente: {str(e)}")
            raise

    async def update(self, client_id: int, client_data: Dict[str, Any]) -> Optional[Client]:
        try:
            client = await self.get_by_id(client_id)
            if not client:
                return None

            # Procesamiento de datos enum
            if 'client_type' in client_data:
                client_data['client_type'] = ClientType(client_data['client_type'])
            if 'status' in client_data:
                client_data['status'] = ClientStatus(client_data['status'])

            # Las fechas ya vienen como datetime del endpoint

            # Actualizar todos los campos proporcionados
            for key, value in client_data.items():
                if hasattr(client, key):
                    setattr(client, key, value)

            client.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(client)
            
            logger.info(f"Cliente actualizado exitosamente: {client.name} (ID: {client.id})")
            return client
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando cliente {client_id}: {str(e)}")
            raise

    async def delete(self, client_id: int) -> bool:
        """Elimina un cliente por su ID."""
        try:
            client = await self.get_by_id(client_id)
            if client:
                self.db.delete(client)
                self.db.commit()
                logger.info(f"Cliente eliminado exitosamente: {client_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error eliminando cliente {client_id}: {str(e)}")
            raise

    async def get_count(self) -> int:
        """Obtiene el número total de clientes."""
        try:
            return self.db.query(Client).count()
        except Exception as e:
            logger.error(f"Error obteniendo conteo de clientes: {str(e)}")
            return 0

    async def get_by_status(self, status: ClientStatus) -> List[Client]:
        """Obtiene clientes por estado."""
        return self.db.query(Client).filter(Client.status == status).all()

    async def get_active_contracts(self) -> List[Client]:
        """Obtiene clientes con contratos activos."""
        current_date = datetime.utcnow()
        return self.db.query(Client).filter(
            Client.contract_end_date > current_date,
            Client.is_active == True
        ).all()

    async def update_last_contact(self, client_id: int) -> Optional[Client]:
        """Actualiza la fecha del último contacto."""
        try:
            client = await self.get_by_id(client_id)
            if client:
                client.last_contact_date = datetime.utcnow()
                self.db.commit()
                return client
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando último contacto del cliente {client_id}: {str(e)}")
            raise

    async def get_by_service_level(self, service_level: str) -> List[Client]:
        """Obtiene clientes por nivel de servicio."""
        return self.db.query(Client).filter(Client.service_level == service_level).all()

    async def get_clients_by_account_manager(self, account_manager: str) -> List[Client]:
        """Obtiene clientes por ejecutivo de cuenta."""
        return self.db.query(Client).filter(Client.account_manager == account_manager).all()