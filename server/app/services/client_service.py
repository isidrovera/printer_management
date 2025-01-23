# app/services/client_service.py
from typing import List, Optional
from sqlalchemy.orm import Session
from ..db.models import Client

class ClientService:
    def __init__(self, db: Session):
        self.db = db

    async def get_all(self) -> List[Client]:
        return self.db.query(Client).all()

    async def get_by_id(self, client_id: int) -> Optional[Client]:
        return self.db.query(Client).filter(Client.id == client_id).first()

    async def create(self, name: str) -> Client:
        client = Client(
            name=name,
            token=Client.generate_token()
        )
        self.db.add(client)
        self.db.commit()
        return client

    async def update(self, client_id: int, name: str) -> Optional[Client]:
        client = await self.get_by_id(client_id)
        if client:
            client.name = name
            self.db.commit()
        return client

    async def delete(self, client_id: int) -> bool:
        client = await self.get_by_id(client_id)
        if client:
            self.db.delete(client)
            self.db.commit()
            return True
        return False