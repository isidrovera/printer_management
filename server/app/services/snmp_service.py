# server/app/services/snmp_service.py
import logging
from typing import Any, Dict
import asyncio
import puresnmp  # Cambiamos la importación aquí

logger = logging.getLogger(__name__)

class SNMPService:
    async def get_oid_value(
        self, 
        ip: str, 
        oid: str, 
        community: str = 'public', 
        version: int = 2
    ) -> Any:
        """
        Obtiene el valor de un OID específico de una impresora mediante SNMP.
        
        Args:
            ip: Dirección IP de la impresora
            oid: OID a consultar
            community: Comunidad SNMP (default: 'public')
            version: Versión SNMP (1 o 2, default: 2)
        
        Returns:
            El valor del OID consultado
        """
        try:
            logger.debug(f"Consultando OID {oid} en {ip}")
            
            # puresnmp es síncrono, así que lo ejecutamos en un thread separado
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: get(
                    ip,
                    community,
                    oid,
                    port=161,
                    timeout=2  # Timeout en segundos
                )
            )
            
            # Procesar el resultado según su tipo
            if isinstance(result, bytes):
                return result.decode('utf-8', errors='replace')
            elif isinstance(result, (int, float)):
                return str(result)
            else:
                return str(result)

        except SnmpTimeoutError:
            logger.error(f"Timeout consultando OID {oid} en {ip}")
            raise TimeoutError(f"No se pudo conectar con la impresora en {ip}")
        except Exception as e:
            logger.error(f"Error consultando OID {oid} en {ip}: {str(e)}")
            raise

    async def walk_oid(
        self,
        ip: str,
        oid: str,
        community: str = 'public',
        version: int = 2
    ) -> Dict[str, Any]:
        """
        Realiza un SNMP walk desde un OID base.
        
        Args:
            ip: Dirección IP de la impresora
            oid: OID base para el walk
            community: Comunidad SNMP
            version: Versión SNMP
        
        Returns:
            Diccionario con los resultados del walk
        """
        try:
            logger.debug(f"Realizando SNMP walk desde OID {oid} en {ip}")
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: walk(
                    ip,
                    community,
                    oid,
                    port=161,
                    timeout=2
                )
            )
            
            # Procesar resultados del walk
            processed_results = {}
            for oid_suffix, value in results:
                if isinstance(value, bytes):
                    processed_results[str(oid_suffix)] = value.decode('utf-8', errors='replace')
                else:
                    processed_results[str(oid_suffix)] = str(value)
                    
            return processed_results

        except SnmpTimeoutError:
            logger.error(f"Timeout en SNMP walk para {ip}")
            raise TimeoutError(f"No se pudo conectar con la impresora en {ip}")
        except Exception as e:
            logger.error(f"Error en SNMP walk: {str(e)}")
            raise

    async def get_multiple_oids(
        self, 
        ip: str, 
        oids: Dict[str, str], 
        community: str = 'public', 
        version: int = 2
    ) -> Dict[str, Any]:
        """
        Obtiene valores de múltiples OIDs de una impresora.
        
        Args:
            ip: Dirección IP de la impresora
            oids: Diccionario de OIDs a consultar {nombre: oid}
            community: Comunidad SNMP
            version: Versión SNMP
        
        Returns:
            Diccionario con los valores obtenidos {nombre: valor}
        """
        try:
            results = {}
            for name, oid in oids.items():
                if oid:  # Solo consultar OIDs definidos
                    try:
                        value = await self.get_oid_value(ip, oid, community, version)
                        results[name] = value
                    except TimeoutError:
                        logger.error(f"Timeout en OID {name} para {ip}")
                        results[name] = None
                    except Exception as e:
                        logger.error(f"Error consultando OID {name}: {str(e)}")
                        results[name] = None
            return results
            
        except Exception as e:
            logger.error(f"Error en consulta múltiple de OIDs: {str(e)}")
            raise