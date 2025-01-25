# server/app/api/v1/endpoints/websocket.py
import sys
import logging
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.agent_service import AgentService
from app.db.models import Client
from typing import Dict

# Configuración de logging
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

websocket_logger = logging.getLogger("websocket")
websocket_logger.setLevel(logging.DEBUG)
websocket_logger.addHandler(handler)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.agent_connections: Dict[str, WebSocket] = {}
        self.status_connections: Dict[str, WebSocket] = {}
        self.logger = logging.getLogger(__name__)

    async def connect_agent(self, agent_token: str, websocket: WebSocket):
        self.logger.info(f"Agent {agent_token} connecting...")
        await websocket.accept()
        self.agent_connections[agent_token] = websocket
        self.logger.info(f"Agent {agent_token} connected successfully")

    async def connect_status(self, websocket: WebSocket):
        self.logger.info("Status connection attempt...")
        await websocket.accept()
        conn_id = id(websocket)
        self.status_connections[conn_id] = websocket
        self.logger.info(f"Status connection {conn_id} established")

    def disconnect_agent(self, agent_token: str):
        self.logger.info(f"Disconnecting agent {agent_token}")
        if agent_token in self.agent_connections:
            del self.agent_connections[agent_token]
            self.logger.info(f"Agent {agent_token} disconnected")
        else:
            self.logger.warning(f"Agent {agent_token} not found in connections")

    def disconnect_status(self, websocket: WebSocket):
        conn_id = id(websocket)
        self.logger.info(f"Disconnecting status connection {conn_id}")
        if conn_id in self.status_connections:
            del self.status_connections[conn_id]
            self.logger.info(f"Status connection {conn_id} removed")
        else:
            self.logger.warning(f"Status connection {conn_id} not found")

    async def broadcast_status(self, message: str):
        self.logger.info(f"Broadcasting status: {message}")
        for conn_id, connection in self.status_connections.items():
            try:
                await connection.send_text(message)
                self.logger.debug(f"Message sent to connection {conn_id}")
            except Exception as e:
                self.logger.error(f"Error sending to connection {conn_id}: {e}")

manager = ConnectionManager()

@router.websocket("/api/v1/ws/register")
async def register_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    Endpoint para registrar un agente.
    """
    websocket_logger.debug("Starting WebSocket connection")
    try:
        # Aceptar la conexión del WebSocket
        await websocket.accept()
        websocket_logger.debug("WebSocket connection accepted")

        # Recibir datos del cliente
        try:
            data = await websocket.receive_json()
            websocket_logger.debug(f"Data received: {data}")
        except Exception as e:
            websocket_logger.error(f"Failed to parse JSON from WebSocket: {e}")
            await websocket.close(code=400)  # Código 400 para indicar error en el cliente
            return

        # Validar el client_token
        client_token = data.get('client_token')
        if not client_token:
            websocket_logger.error("No client_token provided in the request")
            await websocket.send_json({"status": "error", "message": "No client_token provided"})
            await websocket.close(code=403)
            return

        websocket_logger.debug(f"Client token received: {client_token}")

        # Consultar el cliente en la base de datos
        client = db.query(Client).filter(
            Client.token == client_token,
            Client.is_active == True
        ).first()

        if not client:
            websocket_logger.error(f"Invalid client token: {client_token}")
            await websocket.send_json({"status": "error", "message": "Invalid client token"})
            await websocket.close(code=403)
            return

        websocket_logger.info(f"Client validated successfully: {client_token}")

        # Registrar el agente
        system_info = data.get('system_info', {})
        websocket_logger.debug(f"System info received: {system_info}")

        agent_service = AgentService(db)
        try:
            agent = await agent_service.register_agent(
                client_token=client_token,
                hostname=system_info.get('hostname', 'unknown'),
                username=system_info.get('username', 'unknown'),
                ip_address=system_info.get('ip_address', 'unknown'),
                device_type=system_info.get('device_type', 'unknown'),
                system_info=system_info
            )
        except HTTPException as e:
            websocket_logger.error(f"Agent registration failed: {e.detail}")
            await websocket.send_json({"status": "error", "message": e.detail})
            await websocket.close(code=403)
            return
        except Exception as e:
            websocket_logger.error(f"Unexpected error during agent registration: {e}")
            websocket_logger.error(traceback.format_exc())
            await websocket.close(code=500)  # Código 500 para errores del servidor
            return

        # Enviar respuesta al cliente
        response = {"status": "success", "agent_token": agent.token}
        websocket_logger.debug(f"Response to send: {response}")
        await websocket.send_json(response)

    except Exception as e:
        websocket_logger.error(f"Critical error: {e}")
        websocket_logger.error(traceback.format_exc())
        if not websocket.client_state.value:
            await websocket.accept()
        await websocket.close(code=403)

@router.websocket("/agent/{agent_token}")
async def agent_websocket(websocket: WebSocket, agent_token: str, db: Session = Depends(get_db)):
    websocket_logger.info(f"Agent websocket connection request: {agent_token}")
    
    agent_service = AgentService(db)
    agent = await agent_service.validate_agent(agent_token)
    
    if not agent:
        websocket_logger.warning(f"Invalid agent token: {agent_token}")
        await websocket.close(code=4001)
        return
    
    websocket_logger.info(f"Agent validated: {agent_token}")
    await manager.connect_agent(agent_token, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            websocket_logger.info(f"Message from agent {agent_token}: {data}")
            await manager.broadcast_status(f"Agent {agent_token}: {data}")
    except WebSocketDisconnect:
        websocket_logger.info(f"Agent {agent_token} disconnected")
        manager.disconnect_agent(agent_token)
    except Exception as e:
        websocket_logger.error(f"Error in agent websocket {agent_token}: {e}")
        manager.disconnect_agent(agent_token)

@router.websocket("/status")
async def status_websocket(websocket: WebSocket):
    websocket_logger.info("Status websocket connection request")
    await manager.connect_status(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            websocket_logger.debug(f"Status message received: {data}")
    except WebSocketDisconnect:
        websocket_logger.info("Status connection disconnected")
        manager.disconnect_status(websocket)
    except Exception as e:
        websocket_logger.error(f"Error in status websocket: {e}")
        manager.disconnect_status(websocket)
