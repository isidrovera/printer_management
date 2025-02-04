# agent\app\services\printer_monitor_service.py
import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any, List
from pysnmp.hlapi import *

logger = logging.getLogger(__name__)

class PrinterMonitorService:
    def __init__(self, server_url: str, agent_id: str = None):
        self.server_url = server_url
        self.agent_id = agent_id
        self.oids_cache = {}
        self.printers_cache = []
        self.last_cache_update = datetime.now()
    async def scan_and_monitor(self) -> Dict[str, Any]:
        """Método de compatibilidad para agent_service"""
        try:
            # Intentar obtener lista del servidor
            printers = await self._get_monitored_printers()
            
            # Si falla, usar lista local
            if not printers:
                logger.info("Usando lista local de impresoras")
                printers = self.known_printers

            if not printers:
                logger.info("No hay impresoras configuradas para monitorear")
                return {'is_printer': False}

            results = []
            for printer in printers:
                try:
                    data = await self.collect_printer_data(
                        ip=printer['ip_address'],
                        brand=printer['brand']
                    )
                    if data:
                        # Intentar actualizar en el servidor
                        success = await self.update_printer_data(
                            printer['ip_address'],
                            printer['brand'],
                            agent_id=0  # O el ID del agente si lo tienes
                        )
                        if success:
                            logger.info(f"Datos actualizados para {printer['ip_address']}")
                        results.append(data)
                except Exception as e:
                    logger.error(f"Error procesando impresora {printer['ip_address']}: {e}")

            return {
                'is_printer': bool(results),
                'printers': results
            }

        except Exception as e:
            logger.error(f"Error en scan_and_monitor: {e}")
            return {'is_printer': False}

    async def _get_monitored_printers(self) -> List[Dict[str, str]]:
        """Obtiene la lista de impresoras a monitorear del servidor"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url}/api/v1/printers/monitored"
                async with session.get(url) as response:
                    if response.status == 200:
                        printers = await response.json()
                        logger.info(f"Obtenidas {len(printers)} impresoras para monitorear")
                        return printers
                    logger.warning(f"Error obteniendo impresoras del servidor: {response.status}")
                    return []
        except Exception as e:
            logger.warning(f"No se pudo obtener lista del servidor: {e}")
            return []

    async def _update_oids_cache(self, brand: str) -> Dict:
        """Actualiza el caché de OIDs del servidor"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url}/api/v1/printer-oids"
                params = {'brand': brand}
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        oids_data = await response.json()
                        # Guardar en caché con timestamp
                        self.oids_cache[brand] = {
                            'timestamp': datetime.utcnow(),
                            'data': oids_data
                        }
                        logger.info(f"OIDs actualizados para {brand}: {len(oids_data)} OIDs")
                        return oids_data
                    logger.error(f"Error obteniendo OIDs: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error actualizando OIDs: {e}")
            return None

    async def _get_oids_for_brand(self, brand: str) -> Dict:
        """Obtiene los OIDs para una marca, actualiza si es necesario"""
        # Verificar si necesitamos actualizar el caché (cada 5 minutos)
        should_update = True
        if brand in self.oids_cache:
            cache_age = datetime.utcnow() - self.oids_cache[brand]['timestamp']
            if cache_age.total_seconds() < 300:  # 5 minutos
                should_update = False

        if should_update:
            await self._update_oids_cache(brand)

        return self.oids_cache.get(brand, {}).get('data', {})

    async def _get_snmp_values(self, ip: str, oids_data: Dict) -> Dict[str, Any]:
        """Obtiene múltiples valores SNMP de forma eficiente"""
        results = {}
        try:
            logger.debug(f"Obteniendo valores SNMP para {ip}")
            # Extraer OIDs del diccionario recibido
            oids = oids_data.get('oids', {})
            if not oids:
                logger.error("No se encontraron OIDs en la configuración")
                return results

            # Crear lista de ObjectTypes para la consulta
            object_types = []
            oid_mapping = {}  # Para mapear OIDs con sus nombres
            for name, oid in oids.items():
                if isinstance(oid, str):
                    object_types.append(ObjectType(ObjectIdentity(oid)))
                    oid_mapping[oid] = name

            if not object_types:
                logger.error("No se pudieron crear ObjectTypes para SNMP")
                return results

            # Realizar consulta SNMP
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                    CommunityData('public'),
                    UdpTransportTarget((ip, 161), timeout=1, retries=0),
                    ContextData(),
                    *object_types)
            )

            if errorIndication:
                logger.error(f"Error SNMP: {errorIndication}")
                return results

            if errorStatus:
                logger.error(f"Error de estado SNMP: {errorStatus}")
                return results

            # Procesar resultados
            for varBind in varBinds:
                oid = str(varBind[0])
                name = oid_mapping.get(oid, oid)
                try:
                    value = varBind[1].prettyPrint()
                    results[name] = value
                    logger.debug(f"Valor obtenido para {name}: {value}")
                except Exception as e:
                    logger.error(f"Error procesando valor para {name}: {e}")

        except Exception as e:
            logger.error(f"Error en consulta SNMP: {e}")

        logger.info(f"Obtenidos {len(results)} valores SNMP")
        return results

    async def collect_printer_data(self, ip: str, brand: str) -> Dict[str, Any]:
        """Recolecta todos los datos disponibles de una impresora"""
        try:
            logger.info(f"Recolectando datos de {ip} ({brand})")
            
            # Obtener OIDs actualizados
            oids_config = await self._get_oids_for_brand(brand)
            if not oids_config:
                logger.error(f"No se encontraron OIDs para {brand}")
                return None

            # Obtener datos SNMP
            values = await self._get_snmp_values(ip, oids_config)
            if not values:
                logger.error(f"No se obtuvieron datos de {ip}")
                return None

            # Estructurar datos
            printer_data = self._process_printer_data(values)
            printer_data.update({
                'ip_address': ip,
                'brand': brand,
                'last_check': datetime.utcnow().isoformat()
            })

            logger.info(f"Datos recolectados de {ip}: {len(values)} valores")
            return printer_data

        except Exception as e:
            logger.error(f"Error recolectando datos: {e}")
            return None

    async def collect_printer_data(self, ip: str, brand: str) -> Dict[str, Any]:
        """Recolecta todos los datos disponibles de una impresora"""
        try:
            logger.info(f"Recolectando datos de {ip} ({brand})")
            
            # Obtener OIDs actualizados
            oids = await self._get_oids_for_brand(brand)
            if not oids:
                logger.error(f"No se encontraron OIDs para {brand}")
                return None

            # Obtener datos SNMP
            raw_data = await self._get_snmp_values(ip, oids)
            if not raw_data:
                logger.error(f"No se obtuvieron datos de {ip}")
                return None

            # Procesar datos
            printer_data = self._process_printer_data(raw_data)
            printer_data.update({
                'ip_address': ip,
                'brand': brand,
                'last_check': datetime.utcnow().isoformat()
            })

            logger.info(f"Datos recolectados de {ip}")
            return printer_data

        except Exception as e:
            logger.error(f"Error recolectando datos: {e}")
            return None

    async def update_printer_data(self, ip: str, brand: str, agent_id: int) -> bool:
        """Actualiza los datos de la impresora en el servidor"""
        try:
            data = await self.collect_printer_data(ip, brand)
            if not data:
                return False

            async with aiohttp.ClientSession() as session:
                url = f"{self.server_url}/api/v1/monitor/printers/update"
                async with session.post(
                    url,
                    params={'agent_id': agent_id},
                    json=data
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"Error actualizando datos: {e}")
            return False