# server/app/api/v1/endpoints/websocket.py
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.agent_service import AgentService
from typing import Dict

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
@router.websocket("/register")
async def register_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    logger.info("Registration attempt started")
    try:
        await websocket.accept()
        data = await websocket.receive_json()
        logger.info(f"Received data: {data}")
        
        # Verificar token en DB
        client = db.query(Client).filter(Client.token == data['client_token']).first()
        logger.info(f"Client found: {client is not None}")
        if not client:
            raise ValueError("Invalid client token")

        agent_service = AgentService(db)
        system_info = data.get('system_info', {})
        agent = await agent_service.register_agent(
            client_token=data['client_token'],
            hostname=system_info.get('hostname'),
            username=system_info.get('username'),
            ip_address=system_info.get('ip_address'),
            device_type=system_info.get('device_type'),
            system_info=system_info
        )
        
        await websocket.send_json({"status": "success", "agent_token": agent.token})
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        await websocket.close(code=403)

@router.websocket("/agent/{agent_token}")
async def agent_websocket(
   websocket: WebSocket,
   agent_token: str,
   db: Session = Depends(get_db)
):
   logger.info(f"Agent websocket connection request: {agent_token}")
   
   agent_service = AgentService(db)
   agent = await agent_service.validate_agent(agent_token)
   
   if not agent:
       logger.warning(f"Invalid agent token: {agent_token}")
       await websocket.close(code=4001)
       return
   
   logger.info(f"Agent validated: {agent_token}")
   await manager.connect_agent(agent_token, websocket)
   
   try:
       while True:
           data = await websocket.receive_json()
           logger.info(f"Message from agent {agent_token}: {data}")
           await manager.broadcast_status(f"Agent {agent_token}: {data}")
   except WebSocketDisconnect:
       logger.info(f"Agent {agent_token} disconnected")
       manager.disconnect_agent(agent_token)
   except Exception as e:
       logger.error(f"Error in agent websocket {agent_token}: {e}")
       manager.disconnect_agent(agent_token)

@router.websocket("/status")
async def status_websocket(websocket: WebSocket):
   logger.info("Status websocket connection request")
   await manager.connect_status(websocket)
   try:
       while True:
           data = await websocket.receive_text()
           logger.debug(f"Status message received: {data}")
   except WebSocketDisconnect:
       logger.info("Status connection disconnected")
       manager.disconnect_status(websocket)
   except Exception as e:
       logger.error(f"Error in status websocket: {e}")
       manager.disconnect_status(websocket)