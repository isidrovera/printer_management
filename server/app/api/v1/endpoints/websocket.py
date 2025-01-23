# server/app/api/v1/endpoints/websocket.py
from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.websocket_manager import ws_manager
from app.services.agent_service import AgentService
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

router = APIRouter()

@router.websocket("/ws/agent/{agent_token}")
async def websocket_endpoint(
    websocket: WebSocket,
    agent_token: str,
    db: Session = Depends(get_db)
):
    agent_service = AgentService(db)
    agent = await agent_service.validate_agent(agent_token)
    
    if not agent:
        await websocket.close(code=4001)
        return
    
    await ws_manager.connect(agent_token, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Procesar mensajes del agente
            await process_agent_message(agent, data, db)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(agent_token)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[id(websocket)] = websocket

    def disconnect(self, websocket: WebSocket):
        del self.active_connections[id(websocket)]

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/status")
async def status_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)