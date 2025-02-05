# agent/app/services/printer_monitor_service.py
import asyncio
import logging
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pysnmp.hlapi import *

logger = logging.getLogger(__name__)

class PrinterMonitorService:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.oids_cache = {}
        self.monitored_printers = set()
        self.last_check = datetime.now()
        
    async def get_monitored_printers(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de impresoras a monitorear del servidor"""
        try:
            logger.info("Obteniendo lista de impresoras del servidor")
            async with aiohttp.ClientSession() as session:
                # Agregar el agent_id como parámetro de consulta
                url = f"{self.server_url}/api/v1/monitor/printers"
                params = {'agent_id': settings.AGENT_ID} if settings.AGENT_ID else None
                
                headers = {
                    "Authorization": f"Bearer {settings.AGENT_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        printers = await response.json()
                        logger.info(f"Se obtuvieron {len(printers)} impresoras para monitorear")
                        self.monitored_printers = set(p['ip_address'] for p in printers)
                        return printers
                    else:
                        error_text = await response.text()
                        logger.error(f"Error obteniendo impresoras: {response.status} - {error_text}")
                        return []
            except Exception as e:
                logger.error(f"Error en get_monitored_printers: {e}")
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
                return self.oids_cache[brand]

            logger.info(f"Obteniendo OIDs para marca {brand}")
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url}/api/v1/printer-oids/brand/{brand}"
                async with session.get(url) as response:
                    if response.status == 200:
                        oids = await response.json()
                        self.oids_cache[brand] = oids
                        logger.info(f"OIDs obtenidos y cacheados para {brand}")
                        return oids
                    else:
                        logger.error(f"Error obteniendo OIDs: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error en _get_printer_oids: {e}")
            return None

    async def _get_counter_data(self, ip: str, oids: Dict) -> Dict[str, int]:
        """Obtiene datos de contadores usando SNMP"""
        try:
            counter_data = {
                'total_pages': await self._get_snmp_value(ip, oids['total_pages']),
                'color_pages': await self._get_snmp_value(ip, oids['color_pages']),
                'bw_pages': await self._get_snmp_value(ip, oids['bw_pages']),
            }
            return counter_data
        except Exception as e:
            logger.error(f"Error obteniendo contadores de {ip}: {e}")
            return {}

    async def _get_supplies_data(self, ip: str, oids: Dict) -> Dict[str, Any]:
        """Obtiene datos de suministros usando SNMP"""
        try:
            supplies_data = {
                'toners': {
                    'black': {
                        'level': await self._get_snmp_value(ip, oids['black_toner']),
                        'max': await self._get_snmp_value(ip, oids['black_toner_max'])
                    },
                    'cyan': {
                        'level': await self._get_snmp_value(ip, oids['cyan_toner']),
                        'max': await self._get_snmp_value(ip, oids['cyan_toner_max'])
                    },
                    'magenta': {
                        'level': await self._get_snmp_value(ip, oids['magenta_toner']),
                        'max': await self._get_snmp_value(ip, oids['magenta_toner_max'])
                    },
                    'yellow': {
                        'level': await self._get_snmp_value(ip, oids['yellow_toner']),
                        'max': await self._get_snmp_value(ip, oids['yellow_toner_max'])
                    }
                }
            }
            return supplies_data
        except Exception as e:
            logger.error(f"Error obteniendo suministros de {ip}: {e}")
            return {}

    async def _get_snmp_value(self, ip: str, oid: str) -> Any:
        """Obtiene un valor SNMP específico"""
        try:
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

    async def update_printer_data(self, ip: str, data: Dict[str, Any], agent_id: int) -> bool:
        """Envía datos actualizados al servidor"""
        try:
            logger.info(f"Enviando actualización de datos para {ip}")
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url}/api/v1/monitor/printers/update"
                headers = {
                    "Authorization": f"Bearer {settings.AGENT_TOKEN}",
                    "Content-Type": "application/json"
                }
                
                # Incluir agent_id en los datos
                data["agent_id"] = agent_id
                
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"Datos actualizados exitosamente para {ip}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Error actualizando datos para {ip}: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error en update_printer_data para {ip}: {e}")
            return False