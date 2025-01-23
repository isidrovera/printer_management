# server/app/api/v1/endpoints/websocket.py
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

    async def connect_agent(self, agent_token: str, websocket: WebSocket):
        await websocket.accept()
        self.agent_connections[agent_token] = websocket

    async def connect_status(self, websocket: WebSocket):
        await websocket.accept()
        self.status_connections[id(websocket)] = websocket

    def disconnect_agent(self, agent_token: str):
        if agent_token in self.agent_connections:
            del self.agent_connections[agent_token]

    def disconnect_status(self, websocket: WebSocket):
        if id(websocket) in self.status_connections:
            del self.status_connections[id(websocket)]

    async def broadcast_status(self, message: str):
        for connection in self.status_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/agent/{agent_token}")
async def agent_websocket(
    websocket: WebSocket,
    agent_token: str,
    db: Session = Depends(get_db)
):
    agent_service = AgentService(db)
    agent = await agent_service.validate_agent(agent_token)
    
    if not agent:
        await websocket.close(code=4001)
        return
    
    await manager.connect_agent(agent_token, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast_status(f"Agent {agent_token}: {data}")
    except WebSocketDisconnect:
        manager.disconnect_agent(agent_token)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect_agent(agent_token)

@router.websocket("/status")
async def status_websocket(websocket: WebSocket):
    await manager.connect_status(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_status(websocket)