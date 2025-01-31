# server/app/services/tunnel_service.py
from sqlalchemy.orm import Session
from ..db.models.tunnel import Tunnel
from ..db.models.agent import Agent
from ..schemas.tunnel import TunnelCreate
from fastapi import HTTPException
from ..api.v1.endpoints.websocket import manager
import logging
from typing import List, Dict
import asyncio

logger = logging.getLogger(__name__)

class TunnelService:
    def __init__(self, db: Session):
        self.db = db
        self.active_tunnels: Dict[str, dict] = {}

    async def create_tunnel(self, tunnel_data: TunnelCreate) -> dict:
        try:
            agent = self.db.query(Agent).filter(Agent.id == tunnel_data.agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail="Agente no encontrado")

            # Obtener el websocket del manager de conexiones
            websocket = manager.agent_connections.get(agent.token)
            if not websocket:
                raise HTTPException(status_code=503, detail="Agente no está conectado")

            # Crear el ID único del túnel
            tunnel_id = f"{tunnel_data.remote_host}:{tunnel_data.remote_port}-{tunnel_data.local_port}"
            # Verificar túnel existente
            existing_tunnel = self.db.query(Tunnel).filter(
                Tunnel.tunnel_id == tunnel_id,
                Tunnel.status != 'closed'
            ).first()
            
            if existing_tunnel:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Ya existe un túnel activo con ID: {tunnel_id}"
                )
            # Crear registro del túnel
            tunnel = Tunnel(
                agent_id=tunnel_data.agent_id,
                tunnel_id=tunnel_id,
                remote_host=tunnel_data.remote_host,
                remote_port=tunnel_data.remote_port,
                local_port=tunnel_data.local_port,
                status='creating',
                description=tunnel_data.description
            )
            
            self.db.add(tunnel)
            self.db.commit()
            self.db.refresh(tunnel)

            # Enviar comando al agente
            await websocket.send_json({
                'type': 'create_tunnel',
                'tunnel_id': tunnel_id,
                'ssh_host': tunnel_data.ssh_host,
                'ssh_port': tunnel_data.ssh_port,
                'username': tunnel_data.username,
                'password': tunnel_data.password,
                'remote_host': tunnel_data.remote_host,
                'remote_port': tunnel_data.remote_port,
                'local_port': tunnel_data.local_port
            })

            return tunnel

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando túnel: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def close_tunnel(self, tunnel_id: str) -> dict:
        """Cierra un túnel SSH existente."""
        try:
            tunnel = self.db.query(Tunnel).filter(Tunnel.tunnel_id == tunnel_id).first()
            if not tunnel:
                raise HTTPException(status_code=404, detail="Túnel no encontrado")

            agent = self.db.query(Agent).filter(Agent.id == tunnel.agent_id).first()
            if not agent:
                raise HTTPException(status_code=404, detail="Agente no encontrado")

            # Enviar comando de cierre al agente
            await self._send_tunnel_command(agent, 'close_tunnel', {
                'tunnel_id': tunnel_id
            })

            tunnel.status = 'closed'
            self.db.commit()

            return {"message": "Túnel cerrado correctamente"}

        except Exception as e:
            logger.error(f"Error cerrando túnel: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def list_tunnels(self) -> List[Tunnel]:
        """Lista todos los túneles."""
        return self.db.query(Tunnel).all()

    async def _send_tunnel_command(self, agent: Agent, command_type: str, data: dict):
        """Envía un comando al agente a través del WebSocket."""
        if agent.websocket:
            message = {
                'type': command_type,
                **data
            }
            await agent.websocket.send_json(message)
        else:
            raise HTTPException(status_code=503, detail="Agente no está conectado")