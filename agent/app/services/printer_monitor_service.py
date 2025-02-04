# agent\app\services\printer_monitor_service.py
import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any, List
from pysnmp.hlapi import *

logger = logging.getLogger(__name__)

class PrinterMonitorService:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.oids_cache = {}
        self.last_cache_update = {}
        # Lista de impresoras conocidas (fallback)
        self.known_printers = [
            {
                "ip_address": "192.168.18.79",
                "brand": "Ricoh"
            }
            # Puedes agregar más impresoras aquí
        ]

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

    async def _get_snmp_values(self, ip: str, oids: Dict[str, str]) -> Dict[str, Any]:
        """Obtiene múltiples valores SNMP de forma eficiente"""
        results = {}
        try:
            # Crear lista de ObjectType para consulta múltiple
            object_types = [
                ObjectType(ObjectIdentity(oid))
                for oid in oids.values()
            ]

            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                      CommunityData('public'),
                      UdpTransportTarget((ip, 161), timeout=1, retries=0),
                      ContextData(),
                      *object_types)
            )

            if errorIndication or errorStatus:
                logger.error(f"Error SNMP: {errorIndication or errorStatus}")
                return results

            # Mapear resultados con sus nombres
            for (key, _), value in zip(oids.items(), varBinds):
                try:
                    results[key] = value[1].prettyPrint()
                except Exception as e:
                    logger.debug(f"Error procesando {key}: {e}")

        except Exception as e:
            logger.error(f"Error en consulta SNMP: {e}")

        return results

    def _process_printer_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa los datos crudos en una estructura organizada"""
        processed_data = {
            'printer_data': {
                'counters': {},
                'supplies': {
                    'toners': {},
                    'drums': {},
                    'maintenance_kit': {},
                    'waste_toner_box': {}
                },
                'paper_trays': {},
                'system': {},
                'alerts': [],
                'errors': []
            }
        }

        for key, value in raw_data.items():
            if not value:
                continue

            # Clasificar según el tipo de dato
            if 'toner' in key.lower():
                processed_data['printer_data']['supplies']['toners'][key] = value
            elif 'drum' in key.lower():
                processed_data['printer_data']['supplies']['drums'][key] = value
            elif 'waste' in key.lower():
                processed_data['printer_data']['supplies']['waste_toner_box'][key] = value
            elif 'maintenance' in key.lower():
                processed_data['printer_data']['supplies']['maintenance_kit'][key] = value
            elif 'counter' in key.lower() or 'pages' in key.lower():
                processed_data['printer_data']['counters'][key] = value
            elif 'tray' in key.lower():
                processed_data['printer_data']['paper_trays'][key] = value
            elif 'error' in key.lower():
                if value != '0' and value.lower() != 'ok':
                    processed_data['printer_data']['errors'].append({
                        'code': key,
                        'value': value
                    })
            elif 'alert' in key.lower():
                if value != '0' and value.lower() != 'ok':
                    processed_data['printer_data']['alerts'].append({
                        'code': key,
                        'value': value
                    })
            else:
                processed_data['printer_data']['system'][key] = value

        return processed_data

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