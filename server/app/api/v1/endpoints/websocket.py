# server/app/api/v1/endpoints/websocket.py
import sys
import logging
import json
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.agent_service import AgentService
from app.db.models import Client
from typing import Dict, Optional
from datetime import datetime
import asyncio

# Configuración de logging mejorada
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('websocket.log')
    ]
)

websocket_logger = logging.getLogger("websocket")

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.agent_connections: Dict[str, WebSocket] = {}
        self.status_connections: Dict[str, WebSocket] = {}
        self.logger = logging.getLogger(__name__)
        self.heartbeat_interval = 30  # segundos
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Iniciar tareas de mantenimiento"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Detener tareas de mantenimiento"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self):
        """Tarea periódica para limpiar conexiones muertas"""
        while True:
            try:
                await asyncio.sleep(60)  # Ejecutar cada minuto
                await self._cleanup_dead_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error en cleanup loop: {e}")

    async def _cleanup_dead_connections(self):
        """Limpiar conexiones que ya no responden"""
        for connections in [self.agent_connections, self.status_connections]:
            dead_connections = []
            for id_, ws in connections.items():
                try:
                    await ws.send_json({"type": "ping"})
                except Exception:
                    dead_connections.append(id_)
            
            for id_ in dead_connections:
                if id_ in connections:
                    del connections[id_]
                    self.logger.info(f"Conexión muerta eliminada: {id_}")

    async def connect_agent(self, agent_token: str, websocket: WebSocket):
        try:
            await websocket.accept()
            self.agent_connections[agent_token] = websocket
            self.logger.info(f"Agente {agent_token} conectado exitosamente")
            await self.broadcast_status(json.dumps({
                "type": "agent_status",
                "agent_token": agent_token,
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat()
            }))
        except Exception as e:
            self.logger.error(f"Error conectando agente {agent_token}: {e}")
            raise

    async def connect_status(self, websocket: WebSocket):
        try:
            await websocket.accept()
            conn_id = str(id(websocket))
            self.status_connections[conn_id] = websocket
            self.logger.info(f"Conexión de estado {conn_id} establecida")
            return conn_id
        except Exception as e:
            self.logger.error(f"Error en conexión de estado: {e}")
            raise

    async def disconnect_agent(self, agent_token: str):
        try:
            if agent_token in self.agent_connections:
                ws = self.agent_connections[agent_token]
                await ws.close()
                del self.agent_connections[agent_token]
                self.logger.info(f"Agente {agent_token} desconectado")
                await self.broadcast_status(json.dumps({
                    "type": "agent_status",
                    "agent_token": agent_token,
                    "status": "disconnected",
                    "timestamp": datetime.utcnow().isoformat()
                }))
        except Exception as e:
            self.logger.error(f"Error desconectando agente {agent_token}: {e}")

    async def disconnect_status(self, conn_id: str):
        try:
            if conn_id in self.status_connections:
                ws = self.status_connections[conn_id]
                await ws.close()
                del self.status_connections[conn_id]
                self.logger.info(f"Conexión de estado {conn_id} cerrada")
        except Exception as e:
            self.logger.error(f"Error cerrando conexión de estado {conn_id}: {e}")

    async def broadcast_status(self, message: str):
        dead_connections = []
        for conn_id, connection in self.status_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"Error enviando a conexión {conn_id}: {e}")
                dead_connections.append(conn_id)

        # Limpiar conexiones muertas
        for conn_id in dead_connections:
            await self.disconnect_status(conn_id)

    async def send_install_printer_command(self, agent_token: str, printer_data: dict):
        if agent_token not in self.agent_connections:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agente {agent_token} no conectado"
            )
        
        try:
            websocket = self.agent_connections[agent_token]
            command = {
                "type": "install_printer",
                "timestamp": datetime.utcnow().isoformat(),
                "data": printer_data
            }
            await websocket.send_json(command)
            self.logger.info(f"Comando de instalación enviado a agente {agent_token}")
        except Exception as e:
            self.logger.error(f"Error enviando comando a agente {agent_token}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error enviando comando: {str(e)}"
            )

manager = ConnectionManager()

# Inicializar el manager al arrancar
@router.on_event("startup")
async def startup_event():
    await manager.start()

# Detener el manager al cerrar
@router.on_event("shutdown")
async def shutdown_event():
    await manager.stop()

@router.websocket("/register")
async def register_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    """Endpoint para registrar un agente."""
    websocket_logger.debug("Iniciando intento de conexión WebSocket")
    
    try:
        # Aceptar la conexión
        await websocket.accept()
        websocket_logger.debug("Conexión WebSocket aceptada")
        
        try:
            # Recibir y validar datos
            data = await websocket.receive_json()
            websocket_logger.debug(f"Datos recibidos: {data}")
            
            # Validar client_token
            client_token = data.get('client_token')
            if not client_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se proporcionó client_token"
                )

            # Verificar cliente en la base de datos
            client = db.query(Client).filter(
                Client.token == client_token,
                Client.is_active == True
            ).first()

            if not client:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token de cliente inválido"
                )

            websocket_logger.info(f"Cliente validado: {client_token}")

            # Registrar el agente
            system_info = data.get('system_info', {})
            websocket_logger.debug(f"Información del sistema recibida: {system_info}")

            # Crear o actualizar el agente
            agent_service = AgentService(db)
            agent = await agent_service.register_agent(
                client_token=client_token,
                hostname=system_info.get('hostname', 'unknown'),
                username=system_info.get('username', 'unknown'),
                ip_address=system_info.get('ip_address', 'unknown'),
                device_type=system_info.get('device_type', 'unknown'),
                system_info=system_info
            )

            # Enviar respuesta de éxito
            response = {
                "status": "success",
                "agent_token": agent.token,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_json(response)

            # Mantener la conexión y escuchar mensajes
            while True:
                message = await websocket.receive_json()
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                else:
                    websocket_logger.debug(f"Mensaje recibido: {message}")
                    await websocket.send_json({
                        "status": "received",
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": message
                    })

        except HTTPException as e:
            error_response = {
                "status": "error",
                "detail": e.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_json(error_response)
            await websocket.close(code=4001)
            return

        except WebSocketDisconnect:
            websocket_logger.info("Cliente desconectado")
            return

        except Exception as e:
            websocket_logger.error(f"Error inesperado: {str(e)}")
            websocket_logger.error(traceback.format_exc())
            error_response = {
                "status": "error",
                "detail": "Error interno del servidor",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_json(error_response)
            await websocket.close(code=4002)
            return

    except Exception as e:
        websocket_logger.error(f"Error crítico: {str(e)}")
        websocket_logger.error(traceback.format_exc())
        try:
            await websocket.close(code=4003)
        except:
            pass

@router.websocket("/status")
async def status_websocket(websocket: WebSocket):
    conn_id = None
    try:
        conn_id = await manager.connect_status(websocket)
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            else:
                websocket_logger.debug(f"Mensaje de estado recibido: {data}")
    except WebSocketDisconnect:
        if conn_id:
            await manager.disconnect_status(conn_id)
    except Exception as e:
        websocket_logger.error(f"Error en websocket de estado: {e}")
        if conn_id:
            await manager.disconnect_status(conn_id)

@router.websocket("/agent/{agent_token}")
async def agent_websocket(
    websocket: WebSocket,
    agent_token: str,
    db: Session = Depends(get_db)
):
    try:
        agent_service = AgentService(db)
        agent = await agent_service.validate_agent(agent_token)
        
        if not agent:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        await manager.connect_agent(agent_token, websocket)
        
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                else:
                    websocket_logger.info(f"Mensaje de agente {agent_token}: {data}")
                    await manager.broadcast_status(json.dumps({
                        "type": "agent_message",
                        "agent_token": agent_token,
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
        except WebSocketDisconnect:
            await manager.disconnect_agent(agent_token)
        except Exception as e:
            websocket_logger.error(f"Error en websocket de agente {agent_token}: {e}")
            await manager.disconnect_agent(agent_token)
    except Exception as e:
        websocket_logger.error(f"Error crítico en websocket de agente: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass