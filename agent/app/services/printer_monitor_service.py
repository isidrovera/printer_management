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

# Agregar el directorio raíz al path para importaciones absolutas
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.core.config import settings  # Importación absoluta

logger = logging.getLogger(__name__)

class PrinterMonitorService:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.oids_cache = {}
        self.monitored_printers = set()
        self.last_check = datetime.now()
        logger.info(f"PrinterMonitorService inicializado con URL: {server_url}")
        # Verificar configuración al inicializar
        try:
            logger.debug(f"Verificando configuración:")
            logger.debug(f"  SERVER_URL: {settings.SERVER_URL}")
            logger.debug(f"  CLIENT_TOKEN presente: {'Sí' if settings.CLIENT_TOKEN else 'No'}")
            logger.debug(f"  AGENT_TOKEN presente: {'Sí' if settings.AGENT_TOKEN else 'No'}")
        except Exception as e:
            logger.error(f"Error verificando configuración: {e}")

    async def get_monitored_printers(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de impresoras a monitorear del servidor"""
        try:
            logger.info(f"Obteniendo lista de impresoras del servidor ({self.server_url})")
            
            # Verificar configuración
            if not hasattr(settings, 'AGENT_TOKEN') or not settings.AGENT_TOKEN:
                logger.error("AGENT_TOKEN no está configurado en el .env")
                logger.debug("Configuración actual:")
                logger.debug(f"  SERVER_URL: {settings.SERVER_URL if hasattr(settings, 'SERVER_URL') else 'No definido'}")
                logger.debug(f"  CLIENT_TOKEN: {'Presente' if hasattr(settings, 'CLIENT_TOKEN') else 'No definido'}")
                return []

            headers = {
                "Authorization": f"Bearer {settings.AGENT_TOKEN}",
                "Content-Type": "application/json"
            }
            
            logger.debug(f"Realizando petición GET a: {self.server_url}/api/v1/monitor/printers")
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url}/api/v1/monitor/printers"
                logger.debug(f"URL completa: {url}")
                logger.debug(f"Headers: {headers}")
                
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    logger.debug(f"Código de respuesta: {response.status}")
                    logger.debug(f"Respuesta: {response_text[:200]}...")
                    
                    if response.status == 200:
                        printers = json.loads(response_text)
                        logger.info(f"Se obtuvieron {len(printers)} impresoras")
                        return printers
                    else:
                        logger.error(f"Error {response.status}: {response_text}")
                        return []

        except Exception as e:
            logger.error(f"Error en get_monitored_printers: {str(e)}", exc_info=True)
            return []
    async def collect_printer_data(self, ip: str, brand: str) -> Dict[str, Any]:
        """Recolecta datos de una impresora específica"""
        try:
            logger.info(f"Recolectando datos de impresora {ip} ({brand})")
            
            # Obtener OIDs para la marca
            oids = await self._get_printer_oids(brand)
            if not oids:
                logger.error(f"No se encontraron OIDs para la marca {brand}")
                return None

            # Recolectar datos SNMP
            printer_data = {
                'ip_address': ip,
                'brand': brand,
                'last_check': datetime.utcnow().isoformat(),
                'status': 'online',
                'counters': await self._get_counter_data(ip, oids),
                'supplies': await self._get_supplies_data(ip, oids),
            }

            logger.info(f"Datos recolectados exitosamente para {ip}")
            return printer_data

        except Exception as e:
            logger.error(f"Error recolectando datos de {ip}: {e}")
            return None

    async def _get_printer_oids(self, brand: str) -> Dict:
        """Obtiene la configuración de OIDs para una marca"""
        try:
            # Verificar caché
            if brand in self.oids_cache:
                logger.debug(f"OIDs en caché para {brand}: {self.oids_cache[brand]}")
                return self.oids_cache[brand]

            logger.info(f"Obteniendo OIDs para marca {brand}")
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url}/api/v1/printer-oids/brands/{brand}"
                headers = {
                    "Authorization": f"Bearer {settings.AGENT_TOKEN}",
                    "Content-Type": "application/json"
                }
                async with session.get(url, headers=headers) as response:
                    # Leer texto de respuesta
                    response_text = await response.text()
                    logger.debug(f"Respuesta del servidor (status {response.status}): {response_text}")

                    if response.status == 200:
                        oids = json.loads(response_text)
                        logger.debug(f"OIDs parseados: {json.dumps(oids, indent=2)}")
                        
                        self.oids_cache[brand] = oids
                        logger.info(f"OIDs obtenidos y cacheados para {brand}")
                        return oids
                    else:
                        logger.error(f"Error obteniendo OIDs: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error en _get_printer_oids: {e}")
            return None
    

    async def _get_counter_data(self, ip: str, oids: List[Dict]) -> Dict[str, int]:
        """Obtiene datos de contadores usando SNMP"""
        try:
            logger.debug(f"OIDs recibidos para contadores: {oids}")
            
            # Usar el primer elemento de la lista
            oid_config = oids[0] if oids else {}

            counter_data = {
                'total_pages': await self._get_snmp_value(ip, oid_config.get('oid_total_pages', '')),
                'color_pages': await self._get_snmp_value(ip, oid_config.get('oid_total_color_pages', '')),
                'bw_pages': await self._get_snmp_value(ip, oid_config.get('oid_total_bw_pages', '')),
            }
            
            logger.debug(f"Datos de contadores obtenidos: {counter_data}")
            return counter_data
        except Exception as e:
            logger.error(f"Error obteniendo contadores de {ip}: {e}")
            return {}

    
    async def _get_supplies_data(self, ip: str, oids: List[Dict]) -> Dict[str, Any]:
        """Obtiene datos de suministros usando SNMP"""
        try:
            logger.debug(f"OIDs recibidos para suministros: {oids}")
            
            # Usar el primer elemento de la lista
            oid_config = oids[0] if oids else {}

            supplies_data = {
                'toners': {
                    'black': {
                        'level': await self._get_snmp_value(ip, oid_config.get('oid_black_toner_level', '')),
                        'max': None  # No hay información de máximo nivel en los OIDs actuales
                    },
                    'cyan': {
                        'level': await self._get_snmp_value(ip, oid_config.get('oid_cyan_toner_level', '')),
                        'max': None
                    },
                    'magenta': {
                        'level': await self._get_snmp_value(ip, oid_config.get('oid_magenta_toner_level', '')),
                        'max': None
                    },
                    'yellow': {
                        'level': await self._get_snmp_value(ip, oid_config.get('oid_yellow_toner_level', '')),
                        'max': None
                    }
                }
            }
            
            logger.debug(f"Datos de suministros obtenidos: {supplies_data}")
            return supplies_data
        except Exception as e:
            logger.error(f"Error obteniendo suministros de {ip}: {e}")
            return {}
    async def _get_snmp_value(self, ip: str, oid: str) -> Any:
        """Obtiene un valor SNMP específico"""
        try:
            # Manejar caso de OID nulo
            if not oid:
                logger.warning(f"OID nulo para {ip}")
                return None

            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                    CommunityData('public'),
                    UdpTransportTarget((ip, 161), timeout=2, retries=1),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)))
            )
            
            if errorIndication or errorStatus:
                logger.error(f"Error SNMP para {ip} OID {oid}: {errorIndication or errorStatus}")
                return None

            return varBinds[0][1]
        except Exception as e:
            logger.error(f"Error en consulta SNMP para {ip} OID {oid}: {e}")
            return None

    async def update_printer_data(self, ip: str, data: Dict[str, Any]) -> bool:
        """Envía datos actualizados al servidor"""
        try:
            logger.info(f"Enviando actualización de datos para {ip}")
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url}/api/v1/monitor/printers/update"
                headers = {
                    "Authorization": f"Bearer {settings.AGENT_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(url, json=data, headers=headers) as response:
                    success = response.status == 200
                    if success:
                        logger.info(f"Datos actualizados exitosamente para {ip}")
                    else:
                        logger.error(f"Error actualizando datos para {ip}: {response.status}")
                    return success
                    
        except Exception as e:
            logger.error(f"Error en update_printer_data para {ip}: {e}")
            return False

    def _convert_snmp_value(self, value):
        """Convierte valores SNMP a tipos JSON serializables"""
        try:
            # Si es un objeto de PySnmp, extraer su valor
            if hasattr(value, 'prettyPrint'):
                return int(value.prettyPrint())
            return value
        except Exception:
            return None

    async def update_printer_data(self, ip: str, data: Dict[str, Any]) -> bool:
        """Envía datos actualizados al servidor"""
        try:
            logger.info(f"Enviando actualización de datos para {ip}")
            
            # Convertir valores de contadores
            if 'counters' in data:
                data['counters'] = {
                    k: self._convert_snmp_value(v) 
                    for k, v in data['counters'].items()
                }
            
            # Convertir valores de suministros
            if 'supplies' in data and 'toners' in data['supplies']:
                for color, toner in data['supplies']['toners'].items():
                    toner['level'] = self._convert_snmp_value(toner['level'])
                    toner['max'] = self._convert_snmp_value(toner.get('max'))
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url}/api/v1/monitor/printers/update"
                headers = {
                    "Authorization": f"Bearer {settings.AGENT_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(url, json=data, headers=headers) as response:
                    success = response.status == 200
                    if success:
                        logger.info(f"Datos actualizados exitosamente para {ip}")
                    else:
                        logger.error(f"Error actualizando datos para {ip}: {response.status}")
                    return success
                    
        except Exception as e:
            logger.error(f"Error en update_printer_data para {ip}: {e}")
            return False