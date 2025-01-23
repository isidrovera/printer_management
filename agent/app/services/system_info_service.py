# agent/app/services/system_info_service.py
import platform
import socket
import psutil
import os

class SystemInfoService:
    async def get_system_info(self):
        return {
            'hostname': platform.node(),
            'username': os.getenv('USERNAME') or os.getenv('USER'),
            'ip_address': self._get_ip(),
            'device_type': self._get_device_type(),
            'os': platform.system(),
            'os_version': platform.version(),
            'processor': platform.processor(),
            'ram': f"{round(psutil.virtual_memory().total / (1024**3))}GB",
            'mac_address': ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                   for elements in range(0,2*6,2)][::-1])
        }
    
    def _get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    
    def _get_device_type(self):
        return 'Laptop' if hasattr(psutil, 'sensors_battery') and \
               psutil.sensors_battery() is not None else 'PC'