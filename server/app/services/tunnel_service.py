# server/app/services/tunnel_service.py
from sqlalchemy.orm import Session
from ..db.models.tunnel import Tunnel
from ..db.models.agent import Agent
from ..schemas.tunnel import TunnelCreate
from fastapi import HTTPException
from ..api.v1.endpoints.websocket import manager
from fastapi.responses import JSONResponse
import logging
from typing import List, Dict
import asyncio

logger = logging.getLogger(__name__)

class TunnelService:
    def __init__(self, db: Session):
        self.db = db
        self.active_tunnels: Dict[str, dict] = {}

    # server/app/services/tunnel_service.py
    async def create_tunnel(self, tunnel_data: TunnelCreate) -> dict:
        try:
            logger.debug(f"Creando túnel con datos: {tunnel_data}")
            
            tunnel_id = f"{tunnel_data.remote_host}:{tunnel_data.remote_port}-{tunnel_data.local_port}"
            
            # Verificar túnel existente
            existing_tunnel = self.db.query(Tunnel).filter(
                Tunnel.tunnel_id == tunnel_id,
                Tunnel.status != 'closed'
            ).first()
            
            if existing_tunnel:
                logger.warning(f"Túnel ya existe: {tunnel_id}")
                # Importante: Cambiar de raise HTTPException a return para manejar el error correctamente
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Ya existe un túnel activo con ID: {tunnel_id}"}
                )

            agent = self.db.query(Agent).filter(Agent.id == tunnel_data.agent_id).first()
            if not agent:
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Agente no encontrado"}
                )

            # Verificar conexión WebSocket
            websocket = manager.active_connections.get(agent.token)
            if not websocket:
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Agente no está conectado"}
                )

            # Crear el túnel
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
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error interno: {str(e)}"}
            )

    # server/app/services/tunnel_service.py
    async def close_tunnel(self, tunnel_id: str) -> dict:
        """Cierra un túnel SSH existente."""
        try:
            tunnel = self.db.query(Tunnel).filter(Tunnel.tunnel_id == tunnel_id).first()
            if not tunnel:
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Túnel no encontrado"}
                )

            agent = self.db.query(Agent).filter(Agent.id == tunnel.agent_id).first()
            if not agent:
                return JSONResponse(
                    status_code=404,
                    content={"detail": "Agente no encontrado"}
                )

            # Usar el manager para obtener el websocket
            websocket = manager.active_connections.get(agent.token)
            if not websocket:
                # Si no hay conexión, solo actualizamos el estado
                tunnel.status = 'closed'
                self.db.commit()
                return JSONResponse(
                    status_code=200,
                    content={"message": "Túnel marcado como cerrado"}
                )

            # Enviar comando de cierre al agente
            try:
                await websocket.send_json({
                    'type': 'close_tunnel',
                    'tunnel_id': tunnel_id
                })
            except Exception as e:
                logger.error(f"Error enviando comando de cierre: {e}")

            tunnel.status = 'closed'
            self.db.commit()

            return JSONResponse(
                status_code=200,
                content={"message": "Túnel cerrado correctamente"}
            )

        except Exception as e:
            logger.error(f"Error cerrando túnel: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error cerrando túnel: {str(e)}"}
            )

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