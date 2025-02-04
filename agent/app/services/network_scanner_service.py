# agent\app\services\network_scanner_service.py
from pysnmp.hlapi import *
import logging
import netifaces
import ipaddress
import asyncio

logger = logging.getLogger(__name__)

class NetworkScannerService:
    # OIDs universales para impresoras
    DETECTION_OIDS = [
        '1.3.6.1.2.1.1.1.0',     # sysDescr
        '1.3.6.1.2.1.1.5.0',     # sysName
        '1.3.6.1.2.1.43.5.1.1.16.1'  # Nombre de impresora
    ]

    # OIDs específicos por marca con múltiples intentos
    PRINTER_OIDS = {
        'Ricoh': {
            'detection': ['1.3.6.1.2.1.43.8.2.1.14.1.1', '1.3.6.1.4.1.367.3.2.1.1.1.1'],
            'model': '1.3.6.1.2.1.1.5.0',
            'serial': '1.3.6.1.2.1.43.5.1.1.17.1',
            'counter': '1.3.6.1.2.1.43.10.2.1.4.1.1'
        },
        'Canon': {
            'detection': [
                '1.3.6.1.2.1.43.8.2.1.14.1.1',     # Canon específico
                '1.3.6.1.4.1.1602.1.1.1.1',     # Alternativo
                '1.3.6.1.2.1.43.8.2.1.14.1.1'   # General
            ],
            'model': '1.3.6.1.2.1.1.5.0',
            'serial': '1.3.6.1.2.1.43.5.1.1.17.1',
            'counter': '1.3.6.1.2.1.43.10.2.1.4.1.1'
        },
        'HP': {
            'detection': [
                '1.3.6.1.4.1.11.2.3.9.4.2.1.1.3.3.0',
                '1.3.6.1.2.1.25.3.2.1.3.1',
                '1.3.6.1.2.1.43.5.1.1.16.1'
            ],
            'model': '1.3.6.1.2.1.1.5.0',
            'serial': '1.3.6.1.2.1.43.5.1.1.17.1'
        },
        'Kyocera': {
            'detection': [
                '1.3.6.1.4.1.1347.43.5.1.1.28',
                '1.3.6.1.4.1.1347.40.10.1.1.5',
                '1.3.6.1.2.1.43.5.1.1.16.1'
            ],
            'model': '1.3.6.1.2.1.1.5.0',
            'serial': '1.3.6.1.2.1.43.5.1.1.17.1'
        }
    }

    async def _get_snmp_value(self, ip: str, oid: str):
        """Obtiene un valor SNMP específico"""
        try:
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                      CommunityData('public'),
                      UdpTransportTarget((ip, 161), timeout=1, retries=0),
                      ContextData(),
                      ObjectType(ObjectIdentity(oid)))
            )
            
            if errorIndication or errorStatus:
                return None

            value = varBinds[0][1].prettyPrint()
            if 'No Such Instance' in value or 'No Such Object' in value:
                return None

            return value
        except:
            return None

    async def scan_ip(self, ip: str):
        """Escanea una IP buscando una impresora"""
        try:
            # Detección inicial usando OIDs universales
            printer_info = None
            for oid in self.DETECTION_OIDS:
                value = await self._get_snmp_value(ip, oid)
                if value:
                    description = value
                    manufacturer = self._identify_manufacturer(description)
                    if manufacturer:
                        printer_info = {
                            'ip': ip,
                            'manufacturer': manufacturer,
                            'description': description
                        }
                        break

            if not printer_info:
                return None

            # Verificación específica según fabricante
            if printer_info['manufacturer'] in self.PRINTER_OIDS:
                manufacturer_oids = self.PRINTER_OIDS[printer_info['manufacturer']]
                
                # Verificar OIDs de detección específicos
                detected = False
                for detection_oid in manufacturer_oids['detection']:
                    value = await self._get_snmp_value(ip, detection_oid)
                    if value:
                        detected = True
                        break

                if not detected:
                    return None

                # Obtener información adicional
                for key, oid in manufacturer_oids.items():
                    if key != 'detection':
                        value = await self._get_snmp_value(ip, oid)
                        if value:
                            printer_info[key] = value

                logger.info(f"Impresora {printer_info['manufacturer']} encontrada en {ip}")
                return printer_info

        except Exception as e:
            logger.debug(f"Error escaneando {ip}: {e}")
        return None

    def _identify_manufacturer(self, description: str) -> str:
        """Identifica el fabricante por la descripción"""
        description = description.lower()
        manufacturers = {
            'Ricoh': ['ricoh', 'gestetner', 'nashuatec', 'lanier', 'savin', 'rex-rotary'],
            'HP': ['hp', 'hewlett', 'hewlett-packard'],
            'Canon': ['canon', 'imagerunner', 'imagepress'],
            'Xerox': ['xerox', 'fuji xerox'],
            'Kyocera': ['kyocera', 'ecosys', 'taskalfa'],
            'Konica': ['konica', 'minolta', 'bizhub'],
            'Brother': ['brother'],
            'Epson': ['epson'],
            'Lexmark': ['lexmark']
        }

        for manufacturer, keywords in manufacturers.items():
            if any(keyword in description for keyword in keywords):
                return manufacturer
        return None

    async def scan_network(self):
        """Escanea la red en paralelo"""
        networks = []
        for interface in netifaces.interfaces():
            try:
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        if 'addr' in addr and 'netmask' in addr and not addr['addr'].startswith('127.'):
                            networks.append({
                                'ip': addr['addr'],
                                'netmask': addr['netmask']
                            })
            except:
                continue

        printers = []
        for network in networks:
            logger.info(f"Escaneando red: {network['ip']}/{network['netmask']}")
            cidr = sum(bin(int(x)).count('1') for x in network['netmask'].split('.'))
            net = ipaddress.IPv4Network(f"{network['ip']}/{cidr}", strict=False)

            # Escanear en chunks de 10 IPs
            hosts = list(net.hosts())
            for i in range(0, len(hosts), 10):
                chunk = hosts[i:min(i + 10, len(hosts))]
                tasks = [self.scan_ip(str(ip)) for ip in chunk]
                results = await asyncio.gather(*tasks)
                printers.extend([r for r in results if r])

        return printers

    async def scan_printer(self):
        """Mantiene compatibilidad con la interfaz anterior"""
        printers = await self.scan_network()
        return {'is_printer': bool(printers), 'printers': printers}