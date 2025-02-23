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

    def get_all(self) -> List[Client]:
        """Obtiene todos los clientes."""
        try:
            return self.db.query(Client).filter(Client.is_active == True).all()
        except Exception as e:
            logger.error(f"Error obteniendo todos los clientes: {str(e)}")
            return []

    def count_by_status(self) -> Dict[str, int]:
        """Obtiene conteo de clientes por estado"""
        try:
            counts = {
                "total": 0,
                "active": 0,
                "inactive": 0
            }
            
            clients = self.get_all()
            counts["total"] = len(clients)
            
            for client in clients:
                if client.is_active:
                    counts["active"] += 1
                else:
                    counts["inactive"] += 1
                    
            return counts
        except Exception as e:
            logger.error(f"Error contando clientes por estado: {str(e)}")
            return {
                "total": 0,
                "active": 0,
                "inactive": 0
            }
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


    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Obtiene todas las estadísticas necesarias para el dashboard en una sola consulta.
        """
        try:
            total_clients = await self.get_count()
            
            # Obtener conteos por estado
            active_clients = self.db.query(Client).filter(
                Client.is_active == True
            ).count()
            
            # Obtener conteos por tipo de cliente
            client_types_count = {
                client_type.value: self.db.query(Client).filter(
                    Client.client_type == client_type
                ).count()
                for client_type in ClientType
            }
            
            # Obtener contratos activos
            current_date = datetime.utcnow()
            active_contracts = self.db.query(Client).filter(
                Client.contract_end_date > current_date,
                Client.is_active == True
            ).count()

            stats = {
                "total": total_clients,
                "active": active_clients,
                "inactive": total_clients - active_clients,
                "by_type": client_types_count,
                "active_contracts": active_contracts,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Estadísticas del dashboard obtenidas exitosamente - Total clientes: {total_clients}")
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del dashboard: {str(e)}")
            return {
                "total": 0,
                "active": 0,
                "inactive": 0,
                "by_type": {},
                "active_contracts": 0,
                "error": str(e)
            }

    