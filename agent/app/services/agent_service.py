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
import platform
import socket
import aiohttp
import os
import ctypes
import sys
from ..core.config import settings
from .system_info_service import SystemInfoService
from .printer_service import PrinterService
from .printer_monitor_service import PrinterMonitorService
from ..core.message_queue import MessageQueue, MessagePriority
from .smb_service import SMBScannerService
from datetime import datetime
from ..core.config import settings

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
class AgentStatus:
    ONLINE = "online"
    OFFLINE = "offline"  # PC apagada
    CONNECTION_LOST = "connection_lost"  # PC encendida pero sin conexión
    ERROR = "error"
class AgentService:
    def __init__(self):
        self.system_info = SystemInfoService()
        self.printer_monitor = PrinterMonitorService(settings.SERVER_URL)
        self.printer_service = PrinterService()
        self.smb_service = SMBScannerService()
        self.reconnect_interval = 10
        self.system_info = SystemInfoService()
        self.max_reconnect_interval = 300  # 5 minutos máximo entre intentos
        self.active_tunnels = {}
        self.is_shutting_down = False
        self.current_status = AgentStatus.OFFLINE
        self.message_queue = MessageQueue()
        
        
    
    async def start(self):
        """Inicia el agente, registrándolo si es necesario y configura el servicio SMB."""
        logger.info("Iniciando el agente y servicios...")
        import win32api
        def handle_shutdown(sig):
            self.is_shutting_down = True
            self.current_status = AgentStatus.OFFLINE
            asyncio.create_task(self._notify_shutdown())
            return True
            
        win32api.SetConsoleCtrlHandler(handle_shutdown, True)
        # Verificar privilegios de administrador
        if not ctypes.windll.shell32.IsUserAnAdmin():
            logger.error("❌ Se requieren privilegios de administrador para ejecutar el agente")
            logger.info("Por favor, ejecute el agente como administrador")
            sys.exit(1)
        
        # Intentar configurar SMB primero
        try:
            logger.info("Iniciando configuración del servicio SMB...")
            smb_setup_result = await self.smb_service.setup()
            if smb_setup_result:
                logger.info("✅ Servicio SMB configurado exitosamente")
            else:
                logger.warning("⚠️ Servicio SMB configurado parcialmente")
        except Exception as e:
            logger.error(f"❌ Error configurando servicio SMB: {e}")
            # No detenemos el agente si falla SMB, solo registramos el error

        # Bucle principal del agente
        while True:
            try:
                if not settings.AGENT_TOKEN:
                    logger.info("Iniciando registro del agente...")
                    await self._register()
                else:
                    logger.info("Conectando agente al servidor...")
                    await self._connect()
            except Exception as e:
                logger.error(f"Error crítico en el inicio del agente: {e}")
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
                        if data.get("token"):
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
        backoff_time = self.reconnect_interval
        max_backoff = 300  # Máximo 5 minutos entre intentos
        
        while True:
            try:
                ws_url = f"{settings.SERVER_URL}/api/v1/ws/agent/{settings.AGENT_TOKEN}"
                logger.debug(f"🔗 Conectando al servidor WebSocket: {ws_url}")
                logger.debug(f"📝 Agent token: {settings.AGENT_TOKEN}")
                logger.debug(f"📝 Client token: {settings.CLIENT_TOKEN}")
                
                # Intentar hacer una validación HTTP del token primero para diagnóstico
                try:
                    http_url = settings.SERVER_URL.replace("wss://", "https://").replace("ws://", "http://")
                    validate_url = f"{http_url}/api/v1/agents/ping"
                    
                    logger.debug(f"📊 Intentando validación HTTP en: {validate_url}")
                    
                    async with aiohttp.ClientSession() as session:
                        headers = {"Authorization": f"Agent {settings.AGENT_TOKEN}"}
                        async with session.get(validate_url, headers=headers) as response:
                            response_text = await response.text()
                            logger.debug(f"🔍 Respuesta validación HTTP: {response.status} - {response_text}")
                            
                            if response.status != 200:
                                logger.warning(f"⚠️ El token podría no ser válido según validación HTTP")
                except Exception as e:
                    logger.error(f"❌ Error en validación HTTP: {e}")
                
                # Crear un contexto SSL para la conexión WSS
                ssl_context = None
                if ws_url.startswith("wss://"):
                    import ssl
                    logger.debug("🔒 Creando contexto SSL para conexión segura")
                    ssl_context = ssl.create_default_context()
                    
                    # Desactivar verificación para debugging - solo en desarrollo
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    logger.debug("⚠️ Verificación SSL desactivada para diagnóstico")
                    
                # Imprimir detalles de la conexión
                extra_args = {"ssl": ssl_context} if ssl_context else {}
                logger.debug(f"🔄 Parámetros adicionales de conexión: {extra_args}")
                
                # Intentar la conexión WebSocket
                logger.debug(f"🚀 Iniciando conexión WebSocket a: {ws_url}")
                async with websockets.connect(
                    ws_url, 
                    ping_interval=20, 
                    ping_timeout=10,
                    **extra_args
                ) as websocket:
                    logger.info("✅ Conectado al servidor WebSocket correctamente.")
                    backoff_time = self.reconnect_interval  # Resetear backoff al conectar exitosamente
                    
                    # Crear y manejar las tareas de forma más controlada
                    tasks = []
                    tasks.append(asyncio.create_task(self._handle_connection(websocket)))
                    tasks.append(asyncio.create_task(self._periodic_updates(websocket)))
                    tasks.append(asyncio.create_task(self._heartbeat_loop(websocket)))
                    
                    try:
                        # Esperar a que cualquier tarea termine o lance una excepción
                        done, pending = await asyncio.wait(
                            tasks,
                            return_when=asyncio.FIRST_EXCEPTION
                        )
                        
                        # Cancelar las tareas pendientes
                        for task in pending:
                            task.cancel()
                            
                        # Propagar cualquier excepción
                        for task in done:
                            if task.exception():
                                raise task.exception()
                                
                    finally:
                        # Asegurarse de que todas las tareas se cancelen
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                                
                        # Esperar a que todas las tareas se cancelen
                        await asyncio.gather(*tasks, return_exceptions=True)

            except (websockets.exceptions.ConnectionClosed, 
                    websockets.exceptions.WebSocketException,
                    ConnectionRefusedError) as e:
                error_message = str(e)
                logger.error(f"🚨 Conexión WebSocket cerrada/fallida: {error_message}")
                
                # Analizar el error para determinar la causa
                if "403" in error_message:
                    logger.error("🔑 Error 403: Posible problema de autenticación o token invalido")
                    logger.error("💡 Sugerencia: Intenta eliminar AGENT_TOKEN del .env para forzar nuevo registro")
                elif "certificate" in error_message.lower():
                    logger.error("🔒 Error de certificado SSL")
                elif "timeout" in error_message.lower():
                    logger.error("⏱️ Timeout en la conexión")
                
                await asyncio.sleep(backoff_time)
                backoff_time = min(backoff_time * 2, max_backoff)
                
            except Exception as e:
                logger.error(f"🚨 Error inesperado en la conexión WebSocket: {e}")
                logger.error(f"🔍 Tipo de error: {type(e)}")
                import traceback
                logger.error(f"📋 Stacktrace:\n{traceback.format_exc()}")
                await asyncio.sleep(backoff_time)

    async def _handle_connection(self, websocket):
        """Maneja la conexión WebSocket activa."""
        try:
            logger.info("Manejador de conexión iniciado")
            while True:
                try:
                    logger.debug("Esperando mensaje del servidor...")
                    message = await websocket.recv()
                    logger.info(f"Mensaje recibido del servidor: {message}")
                    
                    try:
                        data = json.loads(message)
                        message_type = data.get('type')
                        logger.info(f"Procesando mensaje tipo: {message_type}")
                        
                        # Procesar mensaje directamente
                        await self._process_message(data, websocket)
                        
                    except json.JSONDecodeError:
                        logger.error(f"JSON inválido recibido: {message}")
                        continue
                    except Exception as e:
                        logger.error(f"Error procesando mensaje: {str(e)}")
                        await self._send_error_response(websocket, str(e))
                        continue
                        
                except websockets.exceptions.ConnectionClosed as e:
                    logger.error(f"Conexión cerrada por el servidor: {e}")
                    raise
                except Exception as e:
                    logger.error(f"Error en el bucle de mensajes: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fatal en el manejador de conexión: {e}")
            raise

    async def _process_message(self, data, websocket):
        """Procesa los mensajes recibidos del servidor."""
        try:
            message_type = data.get('type')
            logger.info(f"Iniciando procesamiento de mensaje tipo: {message_type}")
            logger.debug(f"Contenido del mensaje: {data}")
            
            if message_type == 'install_printer':
                logger.info("Procesando comando de instalación de impresora")
                await self._handle_printer_installation(data, websocket)
                
            elif message_type == 'heartbeat':
                logger.debug("Procesando heartbeat")
                await self._handle_heartbeat(websocket)
                
            elif message_type == 'create_tunnel':
                logger.info("Procesando creación de túnel")
                await self._handle_tunnel_creation(data, websocket)
                
            elif message_type == 'close_tunnel':
                logger.info("Procesando cierre de túnel")
                await self._handle_tunnel_closure(data, websocket)
                
            elif message_type == 'printer_created':
                logger.info("Procesando notificación de impresora creada")
                await self._handle_printer_created(data, websocket)
                
            elif message_type == 'scan_printers':
                logger.info("Procesando solicitud de escaneo de impresoras")
                await self._handle_printer_scan(data, websocket)
                
            else:
                logger.warning(f"Tipo de mensaje desconocido: {message_type}")
                await self._send_error_response(websocket, f"Tipo de mensaje no soportado: {message_type}")
                
        except Exception as e:
            error_msg = f"Error procesando mensaje: {str(e)}"
            logger.error(error_msg)
            await self._send_error_response(websocket, error_msg)
            # No relanzar la excepción para mantener la conexión viva

    async def _handle_heartbeat(self, websocket):
        """Maneja los mensajes de heartbeat."""
        try:
            response = {
                'type': 'heartbeat_response',
                'status': self.current_status,
                'timestamp': datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(response))
            logger.debug("Heartbeat enviado correctamente")
        except Exception as e:
            logger.error(f"Error sending heartbeat response: {e}")
            raise  # Propagar el error para forzar reconexión
    async def _heartbeat_loop(self, websocket):
        """Mantiene el heartbeat activo con el servidor."""
        heartbeat_interval = 30  # 30 segundos entre heartbeats
        last_heartbeat = 0
        
        try:
            while True:
                current_time = time.time()
                
                # Verificar si es tiempo de enviar heartbeat
                if current_time - last_heartbeat >= heartbeat_interval:
                    try:
                        # Enviar heartbeat
                        await websocket.send(json.dumps({
                            'type': 'heartbeat',
                            'status': self.current_status,
                            'timestamp': datetime.utcnow().isoformat()
                        }))
                        last_heartbeat = current_time
                        
                    except Exception as e:
                        logger.error(f"Error enviando heartbeat: {e}")
                        raise
                        
                # Esperar un tiempo corto antes de la siguiente iteración
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error fatal en heartbeat loop: {e}")
            raise  # Propagar el error para reiniciar la conexión
    async def _send_error_response(self, websocket, error_message: str):
        """Envía una respuesta de error al servidor."""
        try:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': error_message
            }))
        except Exception as e:
            logger.error(f"Error enviando respuesta de error: {e}")
    async def _handle_printer_installation(self, data, websocket):
        """Maneja la instalación de impresoras."""
        try:
            driver_url = data.get('driver_url')
            if not driver_url:
                raise ValueError("Driver URL not provided in the command.")

            printer_ip = data.get('printer_ip')
            manufacturer = data.get('manufacturer')
            model = data.get('model')
            driver_filename = data.get('driver_filename')

            driver_name = os.path.splitext(driver_filename)[0]
            logger.debug(f"Nombre del driver a usar: {driver_name}")

            with tempfile.TemporaryDirectory() as temp_dir:
                driver_path = os.path.join(temp_dir, driver_filename)
                logger.debug(f"Driver se guardará en: {driver_path}")
                
                async with aiohttp.ClientSession() as session:
                    logger.debug(f"Iniciando descarga desde: {driver_url}")
                    async with session.get(driver_url) as response:
                        if response.status != 200:
                            raise Exception(f"Error downloading driver: {response.status}")
                        
                        # Verificar el Content-Type
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/zip' not in content_type.lower():
                            logger.warning(f"Content-Type inesperado: {content_type}")
                        
                        content = await response.read()
                        logger.debug(f"Descargados {len(content)} bytes")
                        
                        # Verificar si el contenido parece un ZIP
                        if len(content) < 4 or content[:4] != b'PK\x03\x04':
                            # Intentar decodificar el contenido para ver qué recibimos
                            try:
                                text_content = content.decode('utf-8')[:200]
                                logger.error(f"Contenido no válido recibido: {text_content}")
                            except:
                                logger.error("Contenido binario no válido recibido")
                            raise Exception("El archivo descargado no es un ZIP válido")
                        
                        with open(driver_path, 'wb') as f:
                            f.write(content)
                        
                        try:
                            with zipfile.ZipFile(driver_path, 'r') as zip_ref:
                                extract_dir = os.path.join(temp_dir, "extracted")
                                os.makedirs(extract_dir, exist_ok=True)
                                zip_ref.extractall(extract_dir)
                                logger.debug(f"ZIP extraído en: {extract_dir}")
                        except Exception as e:
                            logger.error(f"Error con el archivo ZIP: {e}")
                            raise

                        result = await self.printer_service.install(
                            driver_path,
                            printer_ip,
                            manufacturer,
                            model,
                            driver_name
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

    async def _handle_printer_created(self, data, websocket):
        """Maneja la notificación de una nueva impresora creada."""
        try:
            printer_data = data.get('printer_data')
            if not printer_data:
                raise ValueError("Datos de impresora no proporcionados")
            
            logger.info(f"Nueva impresora creada: {printer_data}")
            
            if not all(key in printer_data for key in ['ip_address', 'brand']):
                raise ValueError("Faltan datos requeridos (ip_address o brand)")
                
            collected_data = await self.printer_monitor.collect_printer_data(
                ip=printer_data['ip_address'],
                brand=printer_data['brand']
            )
            
            if collected_data:
                success = await self.printer_monitor.update_printer_data(
                    ip=printer_data['ip_address'],
                    data=collected_data,
                    agent_id=settings.AGENT_ID
                )
                
                response_data = {
                    'type': 'printer_status',
                    'printer_ip': printer_data['ip_address'],
                    'status': 'success' if success else 'error',
                    'message': 'Datos actualizados correctamente' if success else 'Error actualizando datos'
                }
            else:
                response_data = {
                    'type': 'printer_status',
                    'printer_ip': printer_data['ip_address'],
                    'status': 'error',
                    'message': 'No se pudieron obtener datos de la impresora'
                }
                
            await websocket.send(json.dumps(response_data))
            
        except Exception as e:
            error_msg = f"Error procesando nueva impresora: {str(e)}"
            logger.error(error_msg)
            await self._send_error_response(websocket, error_msg)

    async def _handle_printer_scan(self, data, websocket):
        """Maneja una solicitud de escaneo de impresoras."""
        try:
            logger.info("Iniciando escaneo de impresoras")
            
            networks = data.get('networks', [])
            if not networks:
                local_network = await self.system_info.get_network_info()
                networks = [local_network] if local_network else []
            
            discovered_printers = []
            
            for network in networks:
                logger.info(f"Escaneando red: {network}")
                printers = await self.printer_monitor.scan_network(
                    network_ip=network.get('ip'),
                    netmask=network.get('netmask')
                )
                discovered_printers.extend(printers)
            
            await websocket.send(json.dumps({
                'type': 'scan_results',
                'printers': discovered_printers,
                'timestamp': datetime.utcnow().isoformat()
            }))
            
        except Exception as e:
            error_msg = f"Error en escaneo de impresoras: {str(e)}"
            logger.error(error_msg)
            await self._send_error_response(websocket, error_msg)

    async def _periodic_updates(self, websocket):
        """
        Maneja las actualizaciones periódicas mientras la conexión está activa.
        """
        try:
            while True:
                # Actualizar datos de impresoras monitoreadas
                try:
                    printers = await self.printer_monitor.get_monitored_printers()
                    
                    for printer in printers:
                        try:
                            data = await self.printer_monitor.collect_printer_data(
                                ip=printer['ip_address'],
                                brand=printer['brand']
                            )
                            
                            if data is not None:  # Solo actualizar si hay datos válidos
                                await self.printer_monitor.update_printer_data(
                                    ip=printer['ip_address'],
                                    data=data
                                )
                                logger.debug(f"✅ Datos actualizados para {printer['ip_address']}")
                            else:
                                logger.info(f"⚠️ No se actualizaron datos para {printer['ip_address']} (offline)")
                                
                        except Exception as e:
                            logger.error(f"Error procesando impresora {printer['ip_address']}: {e}")
                            continue
                        
                except Exception as e:
                    logger.error(f"Error en actualización de impresoras: {e}")
                
                await asyncio.sleep(300)  # 5 minutos
                
        except Exception as e:
            logger.error(f"Error en actualizaciones periódicas: {e}")
            raise
    async def _update_agent_info(self):
        """Actualiza la información del agente en el servidor."""
        try:
            new_system_info = await self.system_info.get_system_info()
            try:
                new_ip = socket.gethostbyname(socket.gethostname())
                if new_ip == "127.0.0.1":
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

            async with aiohttp.ClientSession() as session:
                async with session.put(f"{settings.SERVER_URL}/api/v1/agents/update", json=update_data) as response:
                    data = await response.json()
                    if response.status == 200:
                        logger.info("✅ Actualización exitosa en el servidor.")
                    else:
                        logger.error(f"❌ Error en la actualización: {data}")

        except Exception as e:
            logger.error(f"🚨 Error en la actualización del agente: {e}")
    
    async def _handle_tunnel_creation(self, data, websocket):
        """Maneja la creación de túneles SSH."""
        try:
            tunnel_id = f"{data['remote_host']}:{data['remote_port']}-{data['local_port']}"
            
            if tunnel_id in self.active_tunnels:
                raise ValueError(f"Ya existe un túnel activo para {tunnel_id}")

            # Registrar el túnel y su websocket
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
        """Crea y mantiene un túnel SSH."""
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
            transport.request_port_forward('', local_port)

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
        """Maneja la transferencia de datos del túnel."""
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
                tunnel_info = self.active_tunnels.pop(tunnel_id)
                
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
        """Envía actualizaciones de estado del túnel al servidor."""
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

    async def _notify_shutdown(self):
        """Notifica al servidor que la PC se está apagando"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{settings.SERVER_URL}/api/v1/agents/{settings.AGENT_TOKEN}/shutdown"
                async with session.post(url) as response:
                    if response.status == 200:
                        logger.info("✅ Servidor notificado del apagado")
        except Exception as e:
            logger.error(f"❌ Error notificando apagado: {e}")
        """Notifica al servidor que la PC se está apagando"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{settings.SERVER_URL}/api/v1/agents/{settings.AGENT_TOKEN}/shutdown"
                async with session.post(url) as response:
                    if response.status == 200:
                        logger.info("✅ Servidor notificado del apagado")
        except Exception as e:
            logger.error(f"❌ Error notificando apagado: {e}")