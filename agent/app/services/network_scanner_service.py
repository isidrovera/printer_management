#agent\app\services\network_scanner_service.py
import asyncio
import ipaddress
import logging
import aiosnmp
from typing import List, Dict
import netifaces

logger = logging.getLogger(__name__)

# Importaciones correctas de pysnmp
from pysnmp.hlapi import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, nextCmd
)
from pysnmp.smi.rfc1902 import ObjectIdentity


class NetworkScannerService:
    TARGET_IP = "192.168.18.79"
    RICOH_OIDS = [
        ObjectIdentity('1.3.6.1.2.1.43.8.2.1.14.1.1'),
        ObjectIdentity('1.3.6.1.2.1.1.1.0'),
        ObjectIdentity('1.3.6.1.2.1.43.5.1.1.17.1')
    ]

    async def scan_printer(self):
        results = {}

        for oid in self.RICOH_OIDS:
            try:
                error_indication, error_status, error_index, var_binds = next(
                    nextCmd(
                        SnmpEngine(),
                        CommunityData('public', mpModel=0),
                        UdpTransportTarget((self.TARGET_IP, 161)),
                        ContextData(),
                        ObjectType(oid)
                    )
                )

                if error_indication:
                    logger.error(f"SNMP Error: {error_indication}")
                    continue
                elif error_status:
                    logger.error(f"SNMP Error: {error_status.prettyPrint()}")
                    continue
                else:
                    for varBind in var_binds:
                        logger.info(f" = ".join([x.prettyPrint() for x in varBind]))
                        results[str(oid)] = varBind[1].prettyPrint()

            except Exception as e:
                logger.error(f"Error querying OID {oid}: {e}")
                continue

        return {'is_printer': bool(results), 'data': results}
