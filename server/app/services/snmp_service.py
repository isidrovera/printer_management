# server/app/services/snmp_service.py
import logging
from typing import Any, Dict
import asyncio
from pysnmp.hlapi.asyncio import *
import pysnmp

logger = logging.getLogger(__name__)

class SNMPService:
    async def get_oid_value(self, ip: str, oid: str, community: str = 'public', version: int = 2) -> Any:
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
            
            # Configurar versión SNMP
            if version == 1:
                snmp_version = 0  # v1
            else:
                snmp_version = 1  # v2c

            # Crear generador para la consulta SNMP
            snmp_engine = SnmpEngine()
            auth_data = CommunityData(community, mpModel=snmp_version)
            transport_target = UdpTransportTarget((ip, 161))
            context_data = ContextData()

            # Realizar consulta
            error_indication, error_status, error_index, var_binds = await getNextRequestObject(
                snmp_engine,
                auth_data,
                transport_target,
                context_data,
                ObjectType(ObjectIdentity(oid))
            )

            if error_indication:
                raise Exception(f"Error SNMP: {error_indication}")
            elif error_status:
                raise Exception(f"Error en OID #{error_index}: {error_status}")
            
            # Procesar respuesta
            for var_bind in var_binds:
                return var_bind[1].prettyPrint()

        except Exception as e:
            logger.error(f"Error consultando OID {oid} en {ip}: {str(e)}")
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
                    except Exception as e:
                        logger.error(f"Error consultando OID {name}: {str(e)}")
                        results[name] = None
            return results
            
        except Exception as e:
            logger.error(f"Error en consulta múltiple de OIDs: {str(e)}")
            raise