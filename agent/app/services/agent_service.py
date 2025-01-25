# agent/app/services/agent_service.py
import logging
import asyncio
import websockets
import json
from ..core.config import settings
from .system_info_service import SystemInfoService
from .printer_service import PrinterService

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        self.system_info = SystemInfoService()
        self.printer_service = PrinterService()
        self.reconnect_interval = 10
    
    async def start(self):
        if not settings.AGENT_TOKEN:
            await self._register()
        else:
            await self._connect()
    
    async def _register(self):
        registration_data = {
            'type': 'registration',
            'client_token': settings.CLIENT_TOKEN,
            'system_info': await self.system_info.get_system_info()
        }

        # Log de datos a enviar
        logger.debug(f"Registration data to send: {json.dumps(registration_data, indent=4)}")
        
        try:
            async with websockets.connect(f"{settings.SERVER_URL}/api/v1/ws/register") as ws:
                await ws.send(json.dumps(registration_data))
                logger.info("Registration data sent successfully.")

                response = await ws.recv()
                logger.debug(f"Response received: {response}")
                data = json.loads(response)
                
                if data.get('status') == 'success':
                    self._save_agent_token(data['agent_token'])
                    await self._connect()
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            await asyncio.sleep(self.reconnect_interval)
            await self._register()
    
    def _save_agent_token(self, token: str):
        logger.info(f"Saving agent token: {token}")
        with open('.env', 'a') as f:
            f.write(f"\nAGENT_TOKEN={token}")
        settings.AGENT_TOKEN = token
    
    async def _connect(self):
        while True:
            try:
                ws_url = f"{settings.SERVER_URL}/api/v1/ws/agent/{settings.AGENT_TOKEN}"
                logger.debug(f"Connecting to WebSocket: {ws_url}")
                async with websockets.connect(ws_url) as ws:
                    await self._handle_connection(ws)
            except Exception as e:
                logger.error(f"Error during connection: {e}")
                await asyncio.sleep(self.reconnect_interval)
    
    async def _handle_connection(self, websocket):
        try:
            while True:
                message = await websocket.recv()
                logger.debug(f"Message received from server: {message}")
                data = json.loads(message)
                
                if data['type'] == 'install_printer':
                    await self._handle_printer_installation(data, websocket)
                elif data['type'] == 'heartbeat':
                    await websocket.send(json.dumps({
                        'type': 'heartbeat_response',
                        'status': 'alive'
                    }))
        except Exception as e:
            logger.error(f"Error in connection handler: {e}")
    
    async def _handle_printer_installation(self, data, websocket):
        try:
            result = await self.printer_service.install(
                data['driver_data'],
                data['printer_ip'],
                data['manufacturer'],
                data['model']
            )
            
            logger.info(f"Printer installation result: {result}")
            await websocket.send(json.dumps({
                'type': 'installation_result',
                'success': result['success'],
                'message': result['message']
            }))
        except Exception as e:
            logger.error(f"Error during printer installation: {e}")
            await websocket.send(json.dumps({
                'type': 'installation_result',
                'success': False,
                'message': str(e)
            }))
