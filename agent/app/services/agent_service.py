# agent/app/services/agent_service.py
import logging
import asyncio
import websockets
import zipfile
import tempfile
import json
import base64
import paramiko
import threading
import select
import time
import tempfile
import platform
import socket
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
        self.active_tunnels = {}
    
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
        """Registra el agente con el servidor o lo actualiza si ya existe."""
        system_info = await self.system_info.get_system_info()
        
        # Obtener la IP de la interfaz Ethernet o WiFi que tenga una IP válida
        ip_address = "0.0.0.0"
        network_info = system_info.get("Red", {})
        
        # Primero intentar con Ethernet
        ethernet = network_info.get("Ethernet", [])
        for interface in ethernet:
            if interface.get("Tipo") == "IPv4" and not interface.get("Dirección", "").startswith("169.254"):
                ip_address = interface.get("Dirección")
                break
        
        # Si no hay IP válida en Ethernet, intentar con WiFi
        if ip_address == "0.0.0.0":
            wifi = network_info.get("Wi-Fi", [])
            for interface in wifi:
                if interface.get("Tipo") == "IPv4" and not interface.get("Dirección", "").startswith("169.254"):
                    ip_address = interface.get("Dirección")
                    break

        registration_data = {
            "client_token": settings.CLIENT_TOKEN,
            "hostname": platform.node(),
            "username": platform.uname().node,
            "ip_address": ip_address,
            "device_type": system_info["Sistema"]["Nombre del SO"],
            "system_info": system_info
        }

        logger.debug(f"🔄 Enviando datos de registro: {json.dumps(registration_data, indent=4)}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{settings.SERVER_URL}/api/v1/agents/register", json=registration_data) as response:
                    response_text = await response.text()
                    logger.debug(f"Respuesta del servidor: {response.status} - {response_text}")
                    
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError:
                        logger.error(f"Respuesta no es JSON válido: {response_text}")
                        return
                    
                    if response.status == 422:
                        logger.error(f"Error de validación: {data}")
                        return
                    
                    if response.status == 200:
                        if data.get("token"):  # Asumiendo que el servidor devuelve el token en esta clave
                            self._save_agent_token(data["token"])
                            logger.info("✅ Registro exitoso, conectando...")
                            await self._connect()
                        else:
                            logger.error(f"❌ Registro exitoso pero no se recibió token: {data}")
                    else:
                        logger.error(f"❌ Registro fallido: {data}")

        except Exception as e:
            logger.error(f"🚨 Error en el registro: {str(e)}")
            if hasattr(e, '__cause__'):
                logger.error(f"Causa: {str(e.__cause__)}")
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
        """Conecta el agente al servidor usando el token existente y mantiene la conexión."""
        while True:
            try:
                ws_url = f"{settings.SERVER_URL}/api/v1/ws/agent/{settings.AGENT_TOKEN}"
                logger.debug(f"🔗 Conectando al servidor WebSocket: {ws_url}")

                async with websockets.connect(ws_url) as websocket:
                    logger.info("✅ Conectado al servidor WebSocket correctamente.")
                    
                    # Manejar la conexión y las actualizaciones en tareas separadas
                    connection_task = asyncio.create_task(self._handle_connection(websocket))
                    update_task = asyncio.create_task(self._periodic_updates(websocket))
                    
                    # Esperar a que cualquiera de las tareas termine
                    await asyncio.gather(connection_task, update_task, return_exceptions=True)

            except websockets.exceptions.ConnectionClosed as e:
                logger.error(f"🚨 Conexión WebSocket cerrada: {e}")
                await asyncio.sleep(self.reconnect_interval)
            except Exception as e:
                logger.error(f"🚨 Error en la conexión WebSocket: {e}")
                await asyncio.sleep(self.reconnect_interval)

    async def _periodic_updates(self, websocket):
        """Maneja las actualizaciones periódicas mientras la conexión está activa."""
        try:
            while True:
                await self._update_agent_info()
                await asyncio.sleep(300)  # 5 minutos entre actualizaciones
        except Exception as e:
            logger.error(f"Error en actualizaciones periódicas: {e}")
            raise
    async def _handle_connection(self, websocket):
        """Maneja la conexión WebSocket activa."""
        try:
            while True:
                message = await websocket.recv()
                logger.debug(f"Mensaje recibido del servidor: {message}")
                
                try:
                    data = json.loads(message)
                    logger.debug(f"Mensaje decodificado: {json.dumps(data, indent=2)}")
                    await self._process_message(data, websocket)
                except json.JSONDecodeError:
                    logger.error(f"JSON inválido recibido: {message}")
                    continue
                except Exception as e:
                    logger.error(f"Error procesando mensaje: {str(e)}")
                    continue

        except websockets.exceptions.ConnectionClosed:
            logger.info("Conexión cerrada por el servidor")
            raise
        except Exception as e:
            logger.error(f"Error en el manejador de conexión: {str(e)}")
            raise

    async def _process_message(self, data, websocket):
        """Procesa los mensajes recibidos del servidor."""
        try:
            message_type = data.get('type')
            logger.debug(f"Procesando mensaje tipo: {message_type}")
            
            if message_type == 'install_printer':
                await self._handle_printer_installation(data, websocket)
            elif message_type == 'heartbeat':
                await self._handle_heartbeat(websocket)
            elif message_type == 'create_tunnel':
                await self._handle_tunnel_creation(data, websocket)
            elif message_type == 'close_tunnel':
                await self._handle_tunnel_closure(data, websocket)
            else:
                logger.warning(f"Tipo de mensaje desconocido: {message_type}")
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            await self._send_error_response(websocket, str(e))

    async def _send_error_response(self, websocket, error_message: str):
        """Envía una respuesta de error al servidor."""
        try:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': error_message
            }))
        except Exception as e:
            logger.error(f"Error enviando respuesta de error: {e}")
    
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

    async def _update_agent_info(self):
        """Obtiene la información actualizada del sistema y la envía al servidor si hay cambios."""
        try:
            import socket  # Asegurar que esté importado

            new_system_info = await self.system_info.get_system_info()

            # 🔍 Obtener la IP correctamente en cualquier sistema operativo
            try:
                new_ip = socket.gethostbyname(socket.gethostname())  # ✅ Método confiable multiplataforma
                if new_ip == "127.0.0.1":  # Si la IP es localhost, buscar una IP real
                    import netifaces
                    interfaces = netifaces.interfaces()
                    for interface in interfaces:
                        addresses = netifaces.ifaddresses(interface)
                        if netifaces.AF_INET in addresses:
                            for addr in addresses[netifaces.AF_INET]:
                                if addr['addr'] != "127.0.0.1":
                                    new_ip = addr['addr']
                                    break
            except Exception as e:
                new_ip = "0.0.0.0"
                logger.error(f"🚨 Error al obtener la IP en el agente: {e}")

            update_data = {
                "agent_token": settings.AGENT_TOKEN,
                "system_info": new_system_info,
                "ip_address": new_ip
            }

            logger.debug(f"🆕 [AGENTE] Enviando actualización al servidor: {json.dumps(update_data, indent=4)}")

            async with aiohttp.ClientSession() as session:
                async with session.put(f"{settings.SERVER_URL}/api/v1/agents/update", json=update_data) as response:
                    data = await response.json()
                    if response.status == 200:
                        logger.info(f"✅ [AGENTE] Actualización exitosa en el servidor.")
                    else:
                        logger.error(f"❌ [AGENTE] Error en la actualización: {data}")

        except Exception as e:
            logger.error(f"🚨 [AGENTE] Error en la actualización del agente: {e}")



    async def _handle_tunnel_creation(self, data, websocket):
        try:
            tunnel_id = f"{data['remote_host']}:{data['remote_port']}-{data['local_port']}"
            
            if tunnel_id in self.active_tunnels:
                raise ValueError(f"Ya existe un túnel activo para {tunnel_id}")

            # Registrar el túnel y su websocket antes de iniciar el thread
            self.active_tunnels[tunnel_id] = {
                'config': data,
                'websocket': websocket,
                'status': 'starting'
            }

            await websocket.send(json.dumps({
                'type': 'tunnel_status',
                'tunnel_id': tunnel_id,
                'status': 'starting',
                'message': 'Iniciando túnel SSH...'
            }))

            # Crear el túnel en un thread separado
            tunnel_thread = threading.Thread(
                target=self._create_tunnel,
                args=(
                    data['ssh_host'],
                    int(data['ssh_port']),
                    data['username'],
                    data['password'],
                    data['remote_host'],
                    int(data['remote_port']),
                    int(data['local_port']),
                    tunnel_id,
                    asyncio.get_event_loop()
                )
            )
            tunnel_thread.daemon = True
            
            # Agregar el thread al diccionario
            self.active_tunnels[tunnel_id]['thread'] = tunnel_thread
            tunnel_thread.start()

        except Exception as e:
            error_msg = f"Error creando túnel SSH: {str(e)}"
            logger.error(error_msg)
            await websocket.send(json.dumps({
                'type': 'tunnel_status',
                'status': 'error',
                'message': error_msg
            }))

    def _create_tunnel(self, ssh_host, ssh_port, username, password, remote_host, remote_port, local_port, tunnel_id, loop):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            logger.info(f"Conectando a {ssh_host}:{ssh_port}")
            ssh.connect(
                ssh_host, 
                port=ssh_port,
                username=username,
                password=password,
                look_for_keys=False
            )
            logger.info("Conexión SSH establecida")

            transport = ssh.get_transport()
            # Establecer el reenvío de puerto remoto
            transport.request_port_forward('', local_port)

            # Manejar el reenvío de tráfico
            def handle_channel():
                while tunnel_id in self.active_tunnels:
                    try:
                        chan = transport.accept()
                        if chan is None:
                            continue
                        sock = socket.socket()
                        try:
                            sock.connect((remote_host, remote_port))
                        except Exception as e:
                            logger.error(f"Error conectando a {remote_host}:{remote_port} - {e}")
                            chan.close()
                            continue

                        self._handle_tunnel(chan, sock)
                    except Exception as e:
                        logger.error(f"Error en el canal: {e}")
                        break

            # Iniciar thread para manejar canales
            handler_thread = threading.Thread(target=handle_channel)
            handler_thread.daemon = True
            handler_thread.start()

            logger.info(f"Túnel remoto establecido: {remote_host}:{remote_port} <- localhost:{local_port}")

            future = asyncio.run_coroutine_threadsafe(
                self._send_tunnel_status(tunnel_id, 'active', 'Túnel establecido'),
                loop
            )
            future.result()

            while tunnel_id in self.active_tunnels:
                if not ssh.get_transport():
                    break
                time.sleep(1)

            transport.cancel_port_forward('', local_port)
            ssh.close()

        except Exception as e:
            error_msg = f"Error en el túnel: {str(e)}"
            logger.error(error_msg)
            future = asyncio.run_coroutine_threadsafe(
                self._send_tunnel_status(tunnel_id, 'error', error_msg),
                loop
            )
            future.result()

    def _handle_tunnel(self, chan, sock):
        while True:
            r, w, x = select.select([sock, chan], [], [])
            if sock in r:
                data = sock.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                sock.send(data)
        chan.close()
        sock.close()

    async def _handle_tunnel_closure(self, data, websocket):
        """Maneja el cierre de túneles SSH."""
        try:
            tunnel_id = data.get('tunnel_id')
            if not tunnel_id:
                raise ValueError("Se requiere tunnel_id")

            if tunnel_id in self.active_tunnels:
                # Marcar el túnel para cierre
                tunnel_info = self.active_tunnels.pop(tunnel_id)
                # El thread se cerrará en la siguiente iteración
                
                await websocket.send(json.dumps({
                    'type': 'tunnel_status',
                    'tunnel_id': tunnel_id,
                    'status': 'closed',
                    'message': 'Túnel cerrado correctamente'
                }))
            else:
                await websocket.send(json.dumps({
                    'type': 'tunnel_status',
                    'tunnel_id': tunnel_id,
                    'status': 'error',
                    'message': 'Túnel no encontrado'
                }))

        except Exception as e:
            error_msg = f"Error cerrando túnel: {str(e)}"
            logger.error(error_msg)
            await websocket.send(json.dumps({
                'type': 'tunnel_status',
                'status': 'error',
                'message': error_msg
            }))

    async def _send_tunnel_status(self, tunnel_id, status, message):
        try:
            if tunnel_id in self.active_tunnels and 'websocket' in self.active_tunnels[tunnel_id]:
                websocket = self.active_tunnels[tunnel_id]['websocket']
                await websocket.send(json.dumps({
                    'type': 'tunnel_status',
                    'tunnel_id': tunnel_id,
                    'status': status,
                    'message': message
                }))
            else:
                logger.error(f"No se encontró websocket para el túnel {tunnel_id}")
        except Exception as e:
            logger.error(f"Error enviando estado del túnel: {e}")