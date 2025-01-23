from fastapi import APIRouter
from app.api.v1.endpoints import agents, websocket

api_router = APIRouter()
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
