# agent/app/services/system_info_service.py
import platform
import psutil
import socket
import uuid
import json
import shutil

class SystemInfoService:
    @staticmethod
    async def get_system_info():
        """Recopila la información detallada del sistema y hardware"""
        try:
            system_info = {
                "Sistema": {
                    "Nombre del SO": platform.system(),
                    "Versión del SO": platform.version(),
                    "Arquitectura": platform.architecture()[0],
                    "Nombre del dispositivo": platform.node(),
                    "Nombre del usuario": platform.uname().node,
                    "Procesador": platform.processor(),
                },
                "CPU": {
                    "Modelo": platform.processor(),
                    "Núcleos físicos": psutil.cpu_count(logical=False),
                    "Núcleos lógicos": psutil.cpu_count(logical=True),
                    "Frecuencia (MHz)": psutil.cpu_freq().max,
                    "Uso actual (%)": psutil.cpu_percent(interval=1),
                },
                "Memoria": {
                    "Total RAM (GB)": round(psutil.virtual_memory().total / (1024 ** 3), 2),
                    "Disponible RAM (GB)": round(psutil.virtual_memory().available / (1024 ** 3), 2),
                    "Uso de RAM (%)": psutil.virtual_memory().percent,
                },
                "Discos": SystemInfoService.get_disk_info(),
                "Red": SystemInfoService.get_network_info(),
                "Batería": SystemInfoService.get_battery_info(),
                "Tarjetas Gráficas": SystemInfoService.get_gpu_info(),
                "Espacio en Disco": SystemInfoService.get_disk_usage()
            }

            return system_info
        except Exception as e:
            return {"error": f"Error al obtener información del sistema: {str(e)}"}

    @staticmethod
    def get_disk_info():
        """Obtiene la información de los discos duros"""
        disk_info = []
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    "Dispositivo": partition.device,
                    "Punto de montaje": partition.mountpoint,
                    "Tipo de sistema de archivos": partition.fstype,
                    "Total (GB)": round(usage.total / (1024 ** 3), 2),
                    "Usado (GB)": round(usage.used / (1024 ** 3), 2),
                    "Disponible (GB)": round(usage.free / (1024 ** 3), 2),
                    "Porcentaje de uso (%)": usage.percent
                })
            except Exception as e:
                continue
        
        return disk_info

    @staticmethod
    def get_network_info():
        """Obtiene la información de la red, incluyendo interfaces y direcciones IP"""
        network_info = {}
        interfaces = psutil.net_if_addrs()
        
        for interface_name, interface_addresses in interfaces.items():
            network_info[interface_name] = []
            for address in interface_addresses:
                if address.family == socket.AF_INET:
                    network_info[interface_name].append({
                        "Tipo": "IPv4",
                        "Dirección": address.address,
                        "Máscara de red": address.netmask,
                        "Broadcast": address.broadcast
                    })
                elif address.family == socket.AF_INET6:
                    network_info[interface_name].append({
                        "Tipo": "IPv6",
                        "Dirección": address.address,
                        "Máscara de red": address.netmask
                    })
                elif address.family == psutil.AF_LINK:
                    network_info[interface_name].append({
                        "Tipo": "MAC",
                        "Dirección": address.address
                    })
        
        return network_info

    @staticmethod
    def get_battery_info():
        """Obtiene la información de la batería si está disponible"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "Porcentaje": battery.percent,
                    "Enchufado": battery.power_plugged
                }
            return "No se encontró batería."
        except AttributeError:
            return "No se encontró batería."

    @staticmethod
    def get_gpu_info():
        """Obtiene información de la GPU si está disponible (requiere PyCUDA o GPUtil)"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            gpu_info = []
            
            for gpu in gpus:
                gpu_info.append({
                    "Nombre": gpu.name,
                    "Memoria Total (MB)": gpu.memoryTotal,
                    "Memoria Libre (MB)": gpu.memoryFree,
                    "Memoria Usada (MB)": gpu.memoryUsed,
                    "Uso de GPU (%)": gpu.load * 100,
                    "Temperatura (°C)": gpu.temperature
                })
            
            return gpu_info if gpu_info else "No se encontraron GPUs."
        except ImportError:
            return "GPUtil no instalado. Instalar con: pip install gputil"

    @staticmethod
    def get_disk_usage():
        """Obtiene el uso de disco en la carpeta del sistema"""
        total, used, free = shutil.disk_usage("/")
        return {
            "Total (GB)": round(total / (1024 ** 3), 2),
            "Usado (GB)": round(used / (1024 ** 3), 2),
            "Libre (GB)": round(free / (1024 ** 3), 2)
        }
