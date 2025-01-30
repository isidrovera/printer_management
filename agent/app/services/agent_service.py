# agent/app/services/agent_service.py
import logging
import asyncio
import websockets
import zipfile
import tempfile
import json
import base64
import tempfile
import aiohttp
import os
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
        """Inicia el agente, registrándolo si es necesario."""
        while True:
            try:
                if not settings.AGENT_TOKEN:
                    await self._register()
                else:
                    await self._connect()
            except Exception as e:
                logger.error(f"Critical error in agent start: {e}")
                await asyncio.sleep(self.reconnect_interval)
    
    async def _register(self):
        """Registra el agente con el servidor."""
        registration_data = {
            'client_token': settings.CLIENT_TOKEN,
            'system_info': await self.system_info.get_system_info()
        }

        logger.debug(f"Registration data to send: {json.dumps(registration_data, indent=4)}")
        
        try:
            ws_url = f"{settings.SERVER_URL}/api/v1/ws/register"
            logger.debug(f"Connecting to registration endpoint: {ws_url}")
            
            async with websockets.connect(ws_url) as ws:
                # Enviar los datos de registro
                await ws.send(json.dumps(registration_data))
                logger.info("Registration data sent successfully.")

                # Esperar la respuesta
                response = await ws.recv()
                logger.debug(f"Response received: {response}")
                data = json.loads(response)
                
                if data.get('status') == 'success':
                    self._save_agent_token(data['agent_token'])
                    logger.info("Registration successful, connecting as agent...")
                    await self._connect()
                else:
                    logger.error(f"Registration failed: {data.get('message', 'Unknown error')}")
                    raise Exception("Registration failed")
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed during registration: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during registration: {e}")
            raise
    
    def _save_agent_token(self, token: str):
        """Guarda el token del agente en el archivo .env y en la configuración."""
        try:
            logger.info(f"Saving agent token: {token}")
            with open('.env', 'a') as f:
                f.write(f"\nAGENT_TOKEN={token}")
            settings.AGENT_TOKEN = token
        except Exception as e:
            logger.error(f"Error saving agent token: {e}")
            raise
    
    async def _connect(self):
        """Conecta el agente al servidor usando el token existente."""
        while True:
            try:
                ws_url = f"{settings.SERVER_URL}/api/v1/ws/agent/{settings.AGENT_TOKEN}"
                logger.debug(f"Connecting to agent endpoint: {ws_url}")
                
                async with websockets.connect(ws_url) as ws:
                    logger.info("Connected to server successfully")
                    await self._handle_connection(ws)
                    
            except websockets.exceptions.ConnectionClosed as e:
                logger.error(f"WebSocket connection closed: {e}")
                await asyncio.sleep(self.reconnect_interval)
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(self.reconnect_interval)
    
    async def _handle_connection(self, websocket):
        """Maneja la conexión WebSocket activa."""
        try:
            while True:
                message = await websocket.recv()
                logger.debug(f"Message received from server: {message}")
                
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                    continue

                await self._process_message(data, websocket)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
            raise
        except Exception as e:
            logger.error(f"Error in connection handler: {e}")
            raise

    async def _process_message(self, data, websocket):
        """Procesa los mensajes recibidos del servidor."""
        try:
            message_type = data.get('type')
            
            if message_type == 'install_printer':
                await self._handle_printer_installation(data, websocket)
            elif message_type == 'heartbeat':
                await self._handle_heartbeat(websocket)
            else:
                logger.warning(f"Unknown message type received: {message_type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._send_error_response(websocket, str(e))
    
    async def _handle_heartbeat(self, websocket):
        """Maneja los mensajes de heartbeat."""
        try:
            await websocket.send(json.dumps({
                'type': 'heartbeat_response',
                'status': 'alive',
                'timestamp': str(asyncio.get_event_loop().time())
            }))
        except Exception as e:
            logger.error(f"Error sending heartbeat response: {e}")
    
    

    async def _handle_printer_installation(self, data, websocket):
        """Maneja la instalación de impresoras."""
        try:
            # Obtener la URL de descarga y otros datos
            driver_url = data.get('driver_url')
            if not driver_url:
                raise ValueError("Driver URL not provided in the command.")

            printer_ip = data.get('printer_ip')
            manufacturer = data.get('manufacturer')
            model = data.get('model')
            driver_filename = data.get('driver_filename')

            # Obtener el nombre del driver sin la extensión
            driver_name = os.path.splitext(driver_filename)[0]
            logger.debug(f"Nombre del driver a usar: {driver_name}")

            # Crear un directorio temporal para la descarga
            with tempfile.TemporaryDirectory() as temp_dir:
                driver_path = os.path.join(temp_dir, driver_filename)
                logger.debug(f"Driver se guardará en: {driver_path}")
                
                # Realizar la descarga
                async with aiohttp.ClientSession() as session:
                    logger.debug(f"Iniciando descarga desde: {driver_url}")
                    async with session.get(driver_url) as response:
                        if response.status != 200:
                            raise Exception(f"Error downloading driver: {response.status}")
                        
                        content = await response.read()
                        logger.debug(f"Descargados {len(content)} bytes")
                        
                        with open(driver_path, 'wb') as f:
                            f.write(content)
                        
                        logger.debug(f"Archivo guardado en {driver_path}")
                        
                        # Verificar el archivo ZIP
                        try:
                            with zipfile.ZipFile(driver_path, 'r') as zip_ref:
                                logger.debug("Contenido del ZIP:")
                                files = zip_ref.namelist()
                                for name in files:
                                    logger.debug(f"- {name}")
                                
                                # Extraer en un subdirectorio
                                extract_dir = os.path.join(temp_dir, "extracted")
                                os.makedirs(extract_dir, exist_ok=True)
                                zip_ref.extractall(extract_dir)
                                logger.debug(f"ZIP extraído en: {extract_dir}")
                                
                                # Listar archivos extraídos
                                for root, dirs, files in os.walk(extract_dir):
                                    logger.debug(f"Contenido de {root}:")
                                    for file in files:
                                        logger.debug(f"- {file}")
                        except Exception as e:
                            logger.error(f"Error con el archivo ZIP: {e}")
                            raise

                        # Instalar la impresora pasando el nombre del driver
                        logger.debug("Iniciando instalación con printer_service")
                        result = await self.printer_service.install(
                            driver_path,
                            printer_ip,
                            manufacturer,
                            model,
                            driver_name  # Pasamos el nombre del driver sin extensión
                        )
                        
                        logger.info(f"Printer installation result: {result}")
                        await websocket.send(json.dumps({
                            'type': 'installation_result',
                            'success': result['success'],
                            'message': result['message']
                        }))

        except Exception as e:
            logger.error(f"Error during printer installation: {e}")
            await self._send_error_response(websocket, f"Error en instalación: {e}")