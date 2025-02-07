# agent/app/services/printer_monitor_service.py
import asyncio
import logging
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pysnmp.hlapi import *
import sys
import os
from ..core.config import settings

# Configurar el encoding para la salida estándar
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Configurar logging con handler que soporte Unicode
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('printer_monitor.log', encoding='utf-8')
    ]
)


logger = logging.getLogger(__name__)

class PrinterMonitorService:
    def __init__(self, server_url: str):
        """
        Inicializa el servicio de monitoreo de impresoras.
        
        Args:
            server_url (str): URL del servidor de monitoreo
        """
        self.server_url = server_url
        self.oids_cache = {}
        self.monitored_printers = set()
        self.last_check = datetime.now()
        self.snmp_community = 'public'
        self.snmp_port = 161
        self.snmp_timeout = 2
        self.snmp_retries = 1
        
        if not settings.AGENT_TOKEN:
            raise ValueError("AGENT_TOKEN no está configurado en settings")
            
        logger.info(f"PrinterMonitorService inicializado con URL: {server_url}")
        logger.debug("Verificando configuración inicial:")
        logger.debug(f"  SERVER_URL: {settings.SERVER_URL}")
        logger.debug(f"  CLIENT_TOKEN presente: {'Sí' if settings.CLIENT_TOKEN else 'No'}")
        logger.debug(f"  AGENT_TOKEN presente: {'Sí' if settings.AGENT_TOKEN else 'No'}")
        logger.debug(f"  SNMP Community: {self.snmp_community}")
        logger.debug(f"  SNMP Port: {self.snmp_port}")
        logger.debug(f"  SNMP Timeout: {self.snmp_timeout}s")
        logger.debug(f"  SNMP Retries: {self.snmp_retries}")

    async def get_monitored_printers(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de impresoras a monitorear del servidor.
        
        Returns:
            List[Dict[str, Any]]: Lista de impresoras monitoreadas
        """
        try:
            logger.info("📝 Obteniendo lista de impresoras del servidor")
            
            if not settings.AGENT_TOKEN:
                logger.error("❌ Error: AGENT_TOKEN no está configurado")
                return []

            headers = {
                "Authorization": f"Bearer {settings.AGENT_TOKEN}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.server_url}/api/v1/monitor/printers"
            logger.debug(f"🔍 Request URL: {url}")
            logger.debug(f"🔑 Headers configurados: {headers}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    logger.debug(f"📥 Respuesta ({response.status}): {response_text[:200]}...")
                    
                    if response.status == 200:
                        printers = json.loads(response_text)
                        logger.info(f"✅ Se obtuvieron {len(printers)} impresoras")
                        logger.debug(f"📋 Lista de impresoras: {json.dumps(printers, indent=2)}")
                        return printers
                    else:
                        logger.error(f"❌ Error {response.status}: {response_text}")
                        return []

        except json.JSONDecodeError as e:
            logger.error(f"❌ Error decodificando JSON: {str(e)}", exc_info=True)
            return []
        except aiohttp.ClientError as e:
            logger.error(f"❌ Error de conexión: {str(e)}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
            return []

    async def collect_printer_data(self, ip: str, brand: str) -> Dict[str, Any]:
        """
        Recolecta datos de una impresora específica.
        
        Args:
            ip (str): Dirección IP de la impresora
            brand (str): Marca de la impresora
            
        Returns:
            Dict[str, Any]: Datos recolectados de la impresora
        """
        try:
            logger.info(f"🔄 Iniciando recolección de datos - IP: {ip}, Marca: {brand}")
            
            # Verificar conexión antes de continuar
            if not await self.check_printer_connection(ip):
                logger.error(f"❌ Impresora {ip} no responde")
                return {
                    'ip_address': ip,
                    'brand': brand,
                    'status': 'offline',
                    'last_check': datetime.utcnow().isoformat(),
                    'error': 'Printer not responding'
                }

            # Obtener OIDs para la marca
            oids = await self._get_printer_oids(brand)
            if not oids:
                logger.error(f"❌ No se encontraron OIDs para la marca {brand}")
                return None

            # Recolectar datos SNMP
            counters = await self._get_counter_data(ip, oids)
            supplies = await self._get_supplies_data(ip, oids)
            status = await self.get_printer_status(ip)
            
            printer_data = {
                'ip_address': ip,
                'brand': brand,
                'last_check': datetime.utcnow().isoformat(),
                'status': status.get('status', 'unknown'),
                'counters': counters,
                'supplies': supplies,
                'error': None
            }

            logger.info(f"✅ Datos recolectados exitosamente para {ip}")
            logger.debug(f"📊 Datos recolectados: {json.dumps(self._convert_nested_snmp_values(printer_data), indent=2)}")
            
            return printer_data

        except Exception as e:
            logger.error(f"❌ Error recolectando datos de {ip}: {str(e)}", exc_info=True)
            return {
                'ip_address': ip,
                'brand': brand,
                'status': 'error',
                'last_check': datetime.utcnow().isoformat(),
                'error': str(e)
            }

    async def _get_printer_oids(self, brand: str) -> List[Dict]:
        """
        Obtiene la configuración de OIDs para una marca de impresora.
        
        Args:
            brand (str): Marca de la impresora
            
        Returns:
            List[Dict]: Lista de configuraciones de OIDs
        """
        try:
            if brand in self.oids_cache:
                logger.debug(f"📎 Usando OIDs cacheados para {brand}")
                return self.oids_cache[brand]

            logger.info(f"🔍 Obteniendo OIDs para marca {brand}")
            headers = {
                "Authorization": f"Bearer {settings.AGENT_TOKEN}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.server_url}/api/v1/printer-oids/brands/{brand}"
            logger.debug(f"🔍 Request URL: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    logger.debug(f"📥 Respuesta OIDs ({response.status}): {response_text}")

                    if response.status == 200:
                        oids = json.loads(response_text)
                        self.oids_cache[brand] = oids
                        logger.info(f"✅ OIDs obtenidos y cacheados para {brand}")
                        logger.debug(f"📋 OIDs: {json.dumps(oids, indent=2)}")
                        return oids
                    else:
                        logger.error(f"❌ Error obteniendo OIDs: {response.status} - {response_text}")
                        return None

        except Exception as e:
            logger.error(f"❌ Error en _get_printer_oids: {str(e)}", exc_info=True)
            return None
    async def _get_counter_data(self, ip: str, oids: List[Dict]) -> Dict[str, int]:
        """
        Obtiene datos de contadores usando SNMP.
        
        Args:
            ip (str): IP de la impresora
            oids (List[Dict]): Lista de OIDs configurados
            
        Returns:
            Dict[str, int]: Datos de contadores
        """
        try:
            logger.debug(f"📊 Obteniendo contadores para {ip}")
            logger.debug(f"🔧 OIDs configurados: {json.dumps(oids, indent=2)}")
            
            oid_config = oids[0] if oids else {}
            
            total_pages = await self._get_snmp_value(ip, oid_config.get('oid_total_pages'))
            color_pages = await self._get_snmp_value(ip, oid_config.get('oid_total_color_pages'))
            bw_pages = await self._get_snmp_value(ip, oid_config.get('oid_total_bw_pages'))
            
            counter_data = {
                'total_pages': self._convert_snmp_value(total_pages),
                'color_pages': self._convert_snmp_value(color_pages),
                'bw_pages': self._convert_snmp_value(bw_pages)
            }
            
            logger.debug(f"📊 Contadores obtenidos para {ip}: {counter_data}")
            return counter_data

        except Exception as e:
            logger.error(f"❌ Error obteniendo contadores de {ip}: {str(e)}", exc_info=True)
            return {}

    async def _get_supplies_data(self, ip: str, oids: List[Dict]) -> Dict[str, Any]:
        """
        Obtiene datos de suministros usando SNMP.
        
        Args:
            ip (str): IP de la impresora
            oids (List[Dict]): Lista de OIDs configurados
            
        Returns:
            Dict[str, Any]: Datos de suministros
        """
        try:
            logger.debug(f"🔋 Obteniendo suministros para {ip}")
            logger.debug(f"🔧 OIDs configurados: {json.dumps(oids, indent=2)}")
            
            oid_config = oids[0] if oids else {}
            
            # Obtener niveles de toner
            black_level = await self._get_snmp_value(ip, oid_config.get('oid_black_toner_level'))
            cyan_level = await self._get_snmp_value(ip, oid_config.get('oid_cyan_toner_level'))
            magenta_level = await self._get_snmp_value(ip, oid_config.get('oid_magenta_toner_level'))
            yellow_level = await self._get_snmp_value(ip, oid_config.get('oid_yellow_toner_level'))
            
            supplies_data = {
                'toners': {
                    'black': {
                        'level': self._convert_snmp_value(black_level),
                        'max': 100
                    },
                    'cyan': {
                        'level': self._convert_snmp_value(cyan_level),
                        'max': 100
                    },
                    'magenta': {
                        'level': self._convert_snmp_value(magenta_level),
                        'max': 100
                    },
                    'yellow': {
                        'level': self._convert_snmp_value(yellow_level),
                        'max': 100
                    }
                }
            }
            
            logger.debug(f"🔋 Suministros obtenidos para {ip}: {supplies_data}")
            return supplies_data

        except Exception as e:
            logger.error(f"❌ Error obteniendo suministros de {ip}: {str(e)}", exc_info=True)
            return {}

    async def _get_snmp_value(self, ip: str, oid: str) -> Any:
        """
        Obtiene un valor SNMP específico.
        
        Args:
            ip (str): IP de la impresora
            oid (str): OID a consultar
            
        Returns:
            Any: Valor SNMP obtenido
        """
        try:
            if not oid:
                logger.warning(f"⚠️ OID nulo para {ip}")
                return None

            logger.debug(f"🔍 Consultando SNMP {ip} - OID: {oid}")
            
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                    CommunityData(self.snmp_community),
                    UdpTransportTarget((ip, self.snmp_port), 
                                     timeout=self.snmp_timeout, 
                                     retries=self.snmp_retries),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)))
            )
            
            if errorIndication:
                logger.error(f"❌ Error SNMP para {ip}: {errorIndication}")
                return None
                
            if errorStatus:
                logger.error(f"❌ Error status SNMP para {ip}: {errorStatus}")
                return None

            if not varBinds or len(varBinds) == 0:
                logger.warning(f"⚠️ No se recibieron datos SNMP para {ip} - {oid}")
                return None

            value = varBinds[0][1]
            logger.debug(f"📥 Valor SNMP obtenido para {ip} - {oid}: {value}")
            return value

        except Exception as e:
            logger.error(f"❌ Error en consulta SNMP para {ip} - {oid}: {str(e)}", exc_info=True)
            return None

    def _convert_snmp_value(self, value: Any) -> Any:
        """
        Convierte valores SNMP a tipos JSON serializables.
        
        Args:
            value (Any): Valor SNMP a convertir
            
        Returns:
            Any: Valor convertido
        """
        try:
            if value is None:
                return None
            
            if hasattr(value, 'prettyPrint'):
                value_str = value.prettyPrint()
                try:
                    # Intentar convertir a entero primero
                    return int(value_str)
                except ValueError:
                    # Si no es un entero, eliminar comillas si las hay
                    return value_str.strip('"\'')
            
            # Si el valor ya es un tipo básico, devolverlo tal cual
            if isinstance(value, (int, float, str, bool)):
                return value
                
            # Para otros tipos, convertir a string
            return str(value)

        except Exception as e:
            logger.error(f"❌ Error convirtiendo valor SNMP: {str(e)}", exc_info=True)
            return None

    def _convert_nested_snmp_values(self, data: Any) -> Any:
        """
        Convierte recursivamente todos los valores SNMP en una estructura de datos.
        
        Args:
            data (Any): Datos a convertir
            
        Returns:
            Any: Datos convertidos
        """
        try:
            if isinstance(data, dict):
                return {k: self._convert_nested_snmp_values(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [self._convert_nested_snmp_values(item) for item in data]
            else:
                return self._convert_snmp_value(data)
                
        except Exception as e:
            logger.error(f"❌ Error en conversión recursiva: {str(e)}", exc_info=True)
            return None

    def _get_agent_id(self) -> int:
        """
        Obtiene el ID numérico del agente desde la base de datos.
        Por ahora devuelve un valor por defecto hasta que conectemos con la BD.
        
        Returns:
            int: ID del agente
        """
        # Por ahora devolveremos 1 hasta que tengamos acceso a la BD
        return 1

    async def update_printer_data(self, ip: str, data: Dict[str, Any]) -> bool:
        """
        Envía datos actualizados al servidor.
        
        Args:
            ip (str): IP de la impresora
            data (Dict[str, Any]): Datos a actualizar
            
        Returns:
            bool: True si la actualización fue exitosa
        """
        try:
            logger.info(f"Preparando actualización de datos para {ip}")
            
            # Obtener los datos de la impresora del servidor
            printers = await self.get_monitored_printers()
            printer_info = next((p for p in printers if p['ip_address'] == ip), None)
            
            if not printer_info:
                logger.error(f"No se encontró información de la impresora {ip} en el servidor")
                return False
            
            # Convertir todos los valores SNMP
            processed_data = self._convert_nested_snmp_values(data)
            
            # Preparar los datos según el formato requerido por el servidor
            update_data = {
                'ip_address': ip,
                'name': printer_info.get('name'),
                'brand': printer_info.get('brand'),
                'model': printer_info.get('model'),
                'client_id': printer_info.get('client_id'),
                'status': processed_data.get('status', 'offline'),
                'last_check': datetime.utcnow().isoformat()
            }
            
            # Agregar datos de monitoreo
            update_data['printer_data'] = {
                'counters': processed_data.get('counters', {}),
                'supplies': processed_data.get('supplies', {}),
                'status': processed_data.get('status', 'offline')
            }
            
            # Validar serialización antes de enviar
            try:
                json.dumps(update_data)
            except Exception as e:
                logger.error(f"Error de serialización para {ip}: {str(e)}")
                return False
            
            async with aiohttp.ClientSession() as session:
                base_url = self.server_url.replace('ws://', 'http://')
                url = f"{base_url}/api/v1/monitor/printers/update"
                
                headers = {
                    "Authorization": f"Bearer {settings.AGENT_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                # Parámetros de consulta requeridos
                params = {
                    'agent_id': str(self._get_agent_id())
                }
                
                logger.debug(f"Enviando datos a {url}")
                logger.debug(f"Headers: {headers}")
                logger.debug(f"Parámetros: {params}")
                logger.debug(f"Datos: {json.dumps(update_data, indent=2)}")
                
                async with session.post(
                    url, 
                    json=update_data, 
                    headers=headers,
                    params=params
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        logger.info(f"Datos actualizados exitosamente para {ip}")
                        return True
                    else:
                        logger.error(f"Error actualizando datos para {ip}")
                        logger.error(f"Status: {response.status}")
                        logger.error(f"Respuesta: {response_text}")
                        return False
                        
        except aiohttp.ClientError as e:
            logger.error(f"Error de conexión actualizando {ip}: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error inesperado actualizando {ip}: {str(e)}", exc_info=True)
            return False
    async def check_printer_connection(self, ip: str) -> bool:
        """
        Verifica si una impresora está conectada y responde.
        
        Args:
            ip (str): IP de la impresora
            
        Returns:
            bool: True si la impresora responde
        """
        try:
            logger.info(f"🔌 Verificando conexión con impresora {ip}")
            
            # OID del sistema - debería responder cualquier dispositivo SNMP
            system_oid = '1.3.6.1.2.1.1.1.0'
            
            response = await self._get_snmp_value(ip, system_oid)
            is_connected = response is not None
            
            if is_connected:
                logger.info(f"✅ Impresora {ip} responde correctamente")
            else:
                logger.warning(f"⚠️ Impresora {ip} no responde")
                
            return is_connected
            
        except Exception as e:
            logger.error(f"❌ Error verificando conexión con {ip}: {str(e)}", exc_info=True)
            return False

    async def get_printer_status(self, ip: str) -> Dict[str, Any]:
        """
        Obtiene el estado actual de una impresora.
        
        Args:
            ip (str): IP de la impresora
            
        Returns:
            Dict[str, Any]: Estado de la impresora
        """
        try:
            logger.info(f"🔍 Obteniendo estado de impresora {ip}")
            
            # OID estándar para estado de impresora
            status_oid = '1.3.6.1.2.1.25.3.5.1.1.1'
            
            status_value = await self._get_snmp_value(ip, status_oid)
            if status_value is None:
                logger.warning(f"⚠️ No se pudo obtener estado de {ip}")
                return {'status': 'unknown', 'details': 'No response'}
            
            status_code = self._convert_snmp_value(status_value)
            
            # Mapeo de códigos de estado
            status_map = {
                1: 'other',
                2: 'unknown',
                3: 'idle',
                4: 'printing',
                5: 'warmup',
                6: 'stopped',
                7: 'offline',
                8: 'error',
                9: 'service_required'
            }
            
            status = {
                'status': status_map.get(status_code, 'unknown'),
                'details': f'Status code: {status_code}',
                'raw_status': status_code
            }
            
            logger.info(f"📊 Estado obtenido para {ip}: {status}")
            return status
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado de {ip}: {str(e)}", exc_info=True)
            return {'status': 'error', 'details': str(e)}