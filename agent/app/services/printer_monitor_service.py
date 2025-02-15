# agent/app/services/printer_monitor_service.py
import asyncio
import logging
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
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
        self.snmp_community = 'public'  # Valor inicial, se actualizará automáticamente
        self.snmp_port = 161
        self.snmp_timeout = 3  # Aumentado a 3 segundos
        self.snmp_retries = 2  # Aumentado a 2 reintentos
        self.last_successful_config = None
        
        # Logging de la configuración inicial
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

            # Obtener OIDs específicos para la marca
            oids = await self._get_printer_oids(brand)
            if not oids:
                logger.error(f"❌ No se encontraron OIDs para la marca {brand}")
                return None

            oid_config = oids[0] if oids else {}
            
            # Debug de la configuración completa de OIDs
            logger.info(f"📋 Configuración de OIDs para {brand}:")
            for key, value in oid_config.items():
                logger.info(f"  {key}: {value}")
            
            # Obtener datos críticos: modelo y número de serie
            model = None
            serial = None
            model_updated = False

            if 'oid_printer_model' in oid_config and oid_config['oid_printer_model']:
                logger.info(f"Intentando obtener modelo con OID: {oid_config['oid_printer_model']}")
                snmp_model = await self._get_snmp_value(ip, oid_config['oid_printer_model'])
                if snmp_model:
                    model = self._convert_snmp_value(snmp_model)
                    model_updated = True
                    logger.info(f"✅ Modelo obtenido vía SNMP: {model} (valor crudo: {snmp_model})")
            else:
                logger.warning(f"No se encontró OID de modelo configurado para {brand}")
            
            if 'oid_serial_number' in oid_config and oid_config['oid_serial_number']:
                logger.info(f"Intentando obtener serie con OID: {oid_config['oid_serial_number']}")
                snmp_serial = await self._get_snmp_value(ip, oid_config['oid_serial_number'])
                if snmp_serial:
                    serial = self._convert_snmp_value(snmp_serial)
                    logger.info(f"✅ Número de serie obtenido vía SNMP: {serial} (valor crudo: {snmp_serial})")
            else:
                logger.warning(f"No se encontró OID de serie configurado para {brand}")

            # Recolectar otros datos SNMP
            counters = await self._get_counter_data(ip, oids)
            supplies = await self._get_supplies_data(ip, oids)
            status = await self.get_printer_status(ip)
            
            # Obtener datos existentes como respaldo
            printers = await self.get_monitored_printers()
            existing_printer = next((p for p in printers if p['ip_address'] == ip), None)

            if existing_printer:
                logger.info("📋 Datos existentes de la impresora:")
                logger.info(f"  Modelo: {existing_printer.get('model')}")
                logger.info(f"  Serie: {existing_printer.get('serial_number')}")

                # Usar valores existentes solo si no obtuvimos nuevos
                if not model:
                    model = existing_printer.get('model')
                    logger.info(f"Usando modelo existente: {model}")
                
                if not serial:
                    serial = existing_printer.get('serial_number')
            
            printer_data = {
                'ip_address': ip,
                'brand': brand,
                'model': model,
                'serial_number': serial,
                'last_check': datetime.utcnow().isoformat(),
                'status': status.get('status', 'unknown'),
                'counters': counters,
                'supplies': supplies,
                'error': None,
                'model_updated': model_updated
            }

            logger.info(f"✅ Datos recolectados exitosamente para {ip}")
            logger.info("📊 Resumen de datos recolectados:")
            logger.info(f"  Modelo final: {printer_data['model']} (actualizado: {model_updated})")
            logger.info(f"  Serie final: {printer_data['serial_number']}")
            logger.info(f"  Estado: {printer_data['status']}")
            logger.info(f"  Contadores: {printer_data['counters']}")
            logger.info(f"  Suministros: {printer_data['supplies']}")
            
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
            
            # Obtener cada contador con su OID específico
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
            
            # Obtener niveles de toner usando OIDs específicos
            toner_data = {}
            toner_colors = ['black', 'cyan', 'magenta', 'yellow']
            
            for color in toner_colors:
                level_oid = oid_config.get(f'oid_{color}_toner_level')
                max_oid = oid_config.get(f'oid_{color}_toner_max')
                
                level = await self._get_snmp_value(ip, level_oid)
                max_level = await self._get_snmp_value(ip, max_oid)
                
                level_value = self._convert_snmp_value(level)
                max_value = self._convert_snmp_value(max_level) or 100
                
                if level_value is not None:
                    percentage = int((level_value / max_value) * 100) if max_value > 0 else 0
                    percentage = min(100, max(0, percentage))  # Asegurar que esté entre 0 y 100
                    
                    toner_data[color] = {
                        'level': level_value,
                        'max': max_value,
                        'percentage': percentage
                    }
                else:
                    toner_data[color] = {
                        'level': 0,
                        'max': max_value,
                        'percentage': 0
                    }
            
            supplies_data = {
                'toners': toner_data
            }
            
            logger.debug(f"🔋 Suministros obtenidos para {ip}: {supplies_data}")
            return supplies_data

        except Exception as e:
            logger.error(f"❌ Error obteniendo suministros de {ip}: {str(e)}", exc_info=True)
            return {}

    async def _get_snmp_value(self, ip: str, oid: str) -> Any:
        """
        Obtiene un valor SNMP específico intentando diferentes versiones (v1, v2c, v3) y credenciales.
        
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

            # Lista de configuraciones a probar
            snmp_configs = [
                # SNMPv1 configs
                lambda: CommunityData('public', mpModel=0),
                lambda: CommunityData('private', mpModel=0),
                
                # SNMPv2c configs
                lambda: CommunityData('public', mpModel=1),
                lambda: CommunityData('private', mpModel=1),
                
                # SNMPv3 configs - Sin autenticación ni privacidad
                lambda: UsmUserData('initial'),
                
                # SNMPv3 - Con autenticación MD5
                lambda: UsmUserData('md5_user', 'authentication123',
                                  authProtocol=usmHMACMD5AuthProtocol),
                
                # SNMPv3 - Con autenticación SHA
                lambda: UsmUserData('sha_user', 'authentication123',
                                  authProtocol=usmHMACSHAAuthProtocol),
                
                # SNMPv3 - Con autenticación y privacidad (MD5 + DES)
                lambda: UsmUserData('md5_des_user', 'authentication123', 'privacy123',
                                  authProtocol=usmHMACMD5AuthProtocol,
                                  privProtocol=usmDESPrivProtocol),
                
                # SNMPv3 - Con autenticación y privacidad (SHA + AES)
                lambda: UsmUserData('sha_aes_user', 'authentication123', 'privacy123',
                                  authProtocol=usmHMACSHAAuthProtocol,
                                  privProtocol=usmAesCfb128Protocol),
                
                # Credenciales comunes de impresoras
                lambda: UsmUserData('admin', 'admin123', 'admin123',
                                  authProtocol=usmHMACSHAAuthProtocol,
                                  privProtocol=usmAesCfb128Protocol),
            ]

            logger.debug(f"🔍 Intentando conexión SNMP con {ip} - OID: {oid}")

            for config_generator in snmp_configs:
                try:
                    auth_data = config_generator()
                    logger.debug(f"Probando configuración SNMP: {auth_data.__class__.__name__}")
                    
                    errorIndication, errorStatus, errorIndex, varBinds = next(
                        getCmd(SnmpEngine(),
                              auth_data,
                              UdpTransportTarget((ip, self.snmp_port),
                                               timeout=self.snmp_timeout,
                                               retries=self.snmp_retries),
                              ContextData(),
                              ObjectType(ObjectIdentity(oid)))
                    )

                    if errorIndication:
                        logger.debug(f"Intento fallido: {errorIndication}")
                        continue

                    if errorStatus:
                        logger.debug(f"Error status: {errorStatus}")
                        continue

                    if not varBinds or len(varBinds) == 0:
                        logger.debug("Sin datos")
                        continue

                    value = varBinds[0][1]
                    logger.info(f"✅ Conexión exitosa con {auth_data.__class__.__name__}")
                    logger.debug(f"📥 Valor SNMP obtenido para {ip} - {oid}: {value}")
                    
                    # Guardar la configuración exitosa
                    self.last_successful_config = auth_data
                    return value

                except Exception as e:
                    logger.debug(f"Error en intento: {str(e)}")
                    continue

            logger.error(f"❌ No se pudo obtener valor SNMP para {ip} después de probar todas las configuraciones")
            return None

        except Exception as e:
            logger.error(f"❌ Error general en consulta SNMP para {ip} - {oid}: {str(e)}", exc_info=True)
            return None

    def _convert_snmp_value(self, value: Any) -> Optional[Union[int, str]]:
        """
        Convierte valores SNMP preservando el formato original según el contexto.
        
        Args:
            value (Any): Valor SNMP a convertir
            
        Returns:
            Optional[Union[int, str]]: Valor convertido o None si no es válido
        """
        try:
            if value is None:
                return None
            
            if hasattr(value, 'prettyPrint'):
                value_str = value.prettyPrint()
                
                # Si está entre comillas, eliminarlas
                if value_str.startswith('"') and value_str.endswith('"'):
                    value_str = value_str[1:-1]
                
                # Si el valor es enteramente numérico, convertirlo a int
                if value_str.isdigit():
                    return int(value_str)
                
                # Si es un valor con caracteres no numéricos, devolverlo tal cual
                return value_str
                
            # Para valores numéricos directos
            if isinstance(value, (int, float)):
                return int(value)
            
            # Para cualquier otro tipo
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
            
            # Debug de los datos que tenemos
            logger.info("🔍 Datos disponibles para actualización:")
            logger.info(f"  - Datos del servidor:")
            logger.info(f"    Modelo: {printer_info.get('model')}")
            logger.info(f"    Serie: {printer_info.get('serial_number')}")
            logger.info(f"  - Datos procesados:")
            logger.info(f"    Modelo: {processed_data.get('model')}")
            logger.info(f"    Serie: {processed_data.get('serial_number')}")
            
            # Asegurarnos de que tenemos un modelo válido
            model = None
            if processed_data.get('model') and processed_data['model'] != 'Unknown':
                model = processed_data['model']
                logger.info(f"Usando modelo de los datos procesados: {model}")
            elif printer_info.get('model'):
                model = printer_info['model']
                logger.info(f"Usando modelo del servidor: {model}")
                
            if not model:
                logger.error("❌ No se encontró un modelo válido para la impresora")
                return False
                
            # Preparar los datos de actualización
            update_data = {
                'ip_address': ip,
                'name': printer_info.get('name'),
                'brand': printer_info.get('brand'),
                'model': model,  # Usar el modelo validado
                'serial_number': processed_data.get('serial_number') or printer_info.get('serial_number'),
                'client_id': printer_info.get('client_id'),
                'status': processed_data.get('status', 'offline'),
                'last_check': datetime.utcnow().isoformat()
            }
            
            # Agregar datos de monitoreo
            update_data['printer_data'] = {
                'counters': processed_data.get('counters', {}),
                'supplies': processed_data.get('supplies', {}),
                'status': processed_data.get('status', 'offline'),
                'model': model,  # También incluir el modelo aquí
                'serial_number': processed_data.get('serial_number') or printer_info.get('serial_number')
            }

            # Debug de los datos que vamos a enviar
            logger.info("📤 Datos que se enviarán al servidor:")
            logger.info(f"  - Modelo final: {update_data['model']}")
            logger.info(f"  - Serie final: {update_data['serial_number']}")
            logger.info(f"  - Estado: {update_data['status']}")
            
            # Validar que tenemos un modelo antes de enviar
            if not update_data.get('model'):
                logger.error("❌ Error: No hay modelo para enviar")
                return False
                
            # Validar serialización antes de enviar
            try:
                json_data = json.dumps(update_data)
                logger.debug(f"JSON a enviar: {json_data}")
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
                
                params = {
                    'agent_id': str(self._get_agent_id())
                }
                
                async with session.post(
                    url, 
                    json=update_data, 
                    headers=headers,
                    params=params
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        logger.info(f"✅ Datos actualizados exitosamente para {ip}")
                        return True
                    else:
                        logger.error(f"❌ Error actualizando datos para {ip}")
                        logger.error(f"Status: {response.status}")
                        logger.error(f"Respuesta: {response_text}")
                        logger.error(f"Datos enviados: {json.dumps(update_data, indent=2)}")
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