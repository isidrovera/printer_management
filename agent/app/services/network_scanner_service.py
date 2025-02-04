# agent\app\services\network_scanner_service.py
from pysnmp.hlapi import *
import logging

logger = logging.getLogger(__name__)

class NetworkScannerService:
    TARGET_IP = "192.168.18.79"
    
    COMMUNITIES = ['public', 'internal', '@ricoh@', 'ricoh', 'monitor']
    PRINTER_OIDS = {
        'model': '.1.3.6.1.2.1.1.5.0',
        'marca': '.1.3.6.1.2.1.43.8.2.1.14.1.2'
    }

    async def scan_printer(self):
        try:
            for community in self.COMMUNITIES:
                logger.info(f"Probando comunidad: {community}")
                try:
                    # Verificar modelo
                    error_indication, error_status, error_index, var_binds = next(
                        getCmd(SnmpEngine(),
                              CommunityData(community, mpModel=0),  # SNMPv1
                              UdpTransportTarget((self.TARGET_IP, 161), timeout=2, retries=1),
                              ContextData(),
                              ObjectType(ObjectIdentity(self.PRINTER_OIDS['model'])))
                    )

                    if error_indication or error_status:
                        continue

                    model = var_binds[0][1].prettyPrint() if var_binds else "Desconocido"
                    
                    # Verificar marca
                    error_indication, error_status, error_index, var_binds = next(
                        getCmd(SnmpEngine(),
                              CommunityData(community, mpModel=0),
                              UdpTransportTarget((self.TARGET_IP, 161), timeout=2, retries=1),
                              ContextData(),
                              ObjectType(ObjectIdentity(self.PRINTER_OIDS['marca'])))
                    )

                    if error_indication or error_status:
                        continue

                    marca = var_binds[0][1].prettyPrint() if var_binds else "Desconocida"

                    logger.info(f"¡Impresora encontrada! Modelo: {model}, Marca: {marca}")
                    return {
                        'is_printer': True,
                        'ip': self.TARGET_IP,
                        'modelo': model,
                        'marca': marca,
                        'comunidad': community
                    }

                except Exception as e:
                    logger.debug(f"Error con comunidad {community}: {e}")
                    continue

            logger.info("No se detectó ninguna impresora")
            return {'is_printer': False}

        except Exception as e:
            logger.error(f"Error general: {e}")
            return {'is_printer': False}