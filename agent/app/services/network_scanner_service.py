# agent\app\services\network_scanner_service.py
import socket
import logging

logger = logging.getLogger(__name__)

class NetworkScannerService:
    TARGET_IP = "192.168.18.79"

    async def scan_printer(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(1)

                # SNMP GET request (v1)
                request = bytes([
                    0x30, 0x26,                         # SEQUENCE
                    0x02, 0x01, 0x00,                   # Version: 1
                    0x04, 0x06] + list("public".encode()) +  # Community: public
                    [0xa0, 0x19,                        # PDU type: GET
                    0x02, 0x01, 0x00,                   # Request ID: 0
                    0x02, 0x01, 0x00,                   # Error status: 0
                    0x02, 0x01, 0x00,                   # Error index: 0
                    0x30, 0x0e,                         # Variable bindings
                    0x30, 0x0c,                         # Variable
                    0x06, 0x08] +                       # Object ID
                    [0x2b, 0x06, 0x01, 0x02, 0x01, 0x01, 0x05, 0x00])  # sysName OID

                sock.sendto(request, (self.TARGET_IP, 161))
                response, _ = sock.recvfrom(1024)

                if response:
                    return {
                        'is_printer': True,
                        'ip': self.TARGET_IP,
                        'model': 'MP C307',  # Basado en el iReasoning MIB Browser
                        'snmp_response': response.hex()
                    }

        except Exception as e:
            logger.error(f"Error escaneando impresora: {e}")

        return {'is_printer': False}