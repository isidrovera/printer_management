# server/app/services/websocket_manager.py
from fastapi import WebSocket
from typing import Dict
from server.app.core.config import settings

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, agent_token: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[agent_token] = websocket
    
    def disconnect(self, agent_token: str):
        if agent_token in self.active_connections:
            del self.active_connections[agent_token]
    
    async def send_message(self, agent_token: str, message: dict):
        if agent_token in self.active_connections:
            try:
                await self.active_connections[agent_token].send_json(message)
            except Exception as e:
                print(f"Error sending message to {agent_token}: {e}")
                self.disconnect(agent_token)

    def get_connection(self, agent_token: str) -> WebSocket:
        return self.active_connections.get(agent_token)

ws_manager = WebSocketManager()