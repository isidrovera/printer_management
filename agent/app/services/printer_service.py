# agent/app/services/printer_service.py
import os
import tempfile
import zipfile
import subprocess
import platform
import logging

class PrinterService:
    async def install(self, driver_data: bytes, printer_ip: str, 
                     manufacturer: str, model: str):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                driver_path = await self._extract_driver(
                    driver_data, temp_dir
                )
                
                if platform.system() == 'Windows':
                    return await self._install_windows(
                        driver_path, printer_ip, manufacturer, model
                    )
                else:
                    return await self._install_linux(
                        driver_path, printer_ip, manufacturer, model
                    )
        except Exception as e:
            logging.error(f"Error installing printer: {str(e)}")
            return {
                'success': False,
                'message': f"Error en instalación: {str(e)}"
            }
    
    async def _extract_driver(self, driver_data: bytes, temp_dir: str):
        zip_path = os.path.join(temp_dir, 'driver.zip')
        with open(zip_path, 'wb') as f:
            f.write(driver_data)
        
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(temp_dir)
            inf_files = [f for f in z.namelist() if f.endswith('.inf')]
            if not inf_files:
                raise Exception("No se encontró archivo .inf")
            return os.path.join(temp_dir, inf_files[0])
    
    async def _install_windows(self, inf_path: str, printer_ip: str, 
                             manufacturer: str, model: str):
        try:
            # 1. Agregar driver al sistema
            subprocess.run([
                'pnputil', '-i', '-a', inf_path
            ], check=True, capture_output=True, text=True)

            # 2. Crear puerto TCP/IP
            port_name = f"IP_{printer_ip}"
            subprocess.run([
                'powershell',
                '-Command',
                f'Add-PrinterPort -Name "{port_name}" ' \
                f'-PrinterHostAddress "{printer_ip}"'
            ], check=True, capture_output=True, text=True)

            # 3. Instalar impresora
            printer_name = f"{manufacturer} {model}"
            subprocess.run([
                'powershell',
                '-Command',
                f'Add-Printer -Name "{printer_name}" ' \
                f'-DriverName "{model}" -PortName "{port_name}"'
            ], check=True, capture_output=True, text=True)

            return {
                'success': True,
                'message': f'Impresora {printer_name} instalada correctamente'
            }
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            return {
                'success': False,
                'message': f"Error en instalación Windows: {error_msg}"
            }
    
    async def _install_linux(self, inf_path: str, printer_ip: str, 
                           manufacturer: str, model: str):
        try:
            # 1. Verificar si CUPS está instalado
            subprocess.run(['lpstat', '-v'], check=True, capture_output=True)

            # 2. Generar nombre único para la impresora
            printer_name = f"{manufacturer}_{model}".replace(' ', '_')

            # 3. Instalar driver si es necesario
            if inf_path.endswith('.ppd'):
                ppd_path = inf_path
            else:
                # Convertir .inf a .ppd si es necesario
                ppd_path = await self._convert_inf_to_ppd(inf_path)

            # 4. Agregar impresora usando lpadmin
            subprocess.run([
                'lpadmin',
                '-p', printer_name,
                '-v', f"socket://{printer_ip}",
                '-P', ppd_path,
                '-E'  # Habilitar la impresora
            ], check=True, capture_output=True, text=True)

            # 5. Establecer como impresora predeterminada (opcional)
            subprocess.run([
                'lpoptions',
                '-d', printer_name
            ], check=True, capture_output=True, text=True)

            return {
                'success': True,
                'message': f'Impresora {printer_name} instalada correctamente en CUPS'
            }
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            return {
                'success': False,
                'message': f"Error en instalación Linux: {error_msg}"
            }
    
    async def _convert_inf_to_ppd(self, inf_path: str) -> str:
        """
        Convierte un archivo .inf a .ppd para sistemas Linux.
        En la práctica, esto podría requerir herramientas adicionales
        o una base de datos de conversión.
        """
        try:
            # Esta es una implementación simplificada
            # En un caso real, necesitarías una herramienta de conversión
            # o una base de datos de equivalencias
            ppd_dir = os.path.dirname(inf_path)
            ppd_path = os.path.join(ppd_dir, 'converted.ppd')
            
            # Aquí iría la lógica real de conversión
            # Por ahora, solo verificamos si existe un PPD junto al INF
            existing_ppd = inf_path.replace('.inf', '.ppd')
            if os.path.exists(existing_ppd):
                return existing_ppd
                
            raise NotImplementedError(
                "Conversión INF a PPD no implementada. " \
                "Se requiere un archivo PPD válido para Linux."
            )
        except Exception as e:
            raise Exception(f"Error en conversión INF a PPD: {str(e)}")

    async def uninstall(self, printer_name: str):
        """
        Desinstala una impresora previamente instalada
        """
        try:
            if platform.system() == 'Windows':
                subprocess.run([
                    'powershell',
                    '-Command',
                    f'Remove-Printer -Name "{printer_name}"'
                ], check=True, capture_output=True, text=True)
            else:
                subprocess.run([
                    'lpadmin',
                    '-x', printer_name
                ], check=True, capture_output=True, text=True)

            return {
                'success': True,
                'message': f'Impresora {printer_name} desinstalada correctamente'
            }
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            return {
                'success': False,
                'message': f"Error en desinstalación: {error_msg}"
            }

    async def list_printers(self):
        """
        Lista las impresoras instaladas en el sistema
        """
        try:
            if platform.system() == 'Windows':
                result = subprocess.run([
                    'powershell',
                    '-Command',
                    'Get-Printer | Select-Object Name,DriverName,PortName | ConvertTo-Json'
                ], check=True, capture_output=True, text=True)
                return {
                    'success': True,
                    'printers': result.stdout
                }
            else:
                result = subprocess.run([
                    'lpstat',
                    '-p'
                ], check=True, capture_output=True, text=True)
                return {
                    'success': True,
                    'printers': result.stdout
                }
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            return {
                'success': False,
                'message': f"Error listando impresoras: {error_msg}"
            }