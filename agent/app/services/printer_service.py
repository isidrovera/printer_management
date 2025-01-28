# agent/app/services/printer_service.py
import os
import tempfile
import zipfile
import subprocess
import platform
import logging

class PrinterService:
    async def install(self, compressed_driver_path: str, printer_ip: str, manufacturer: str, model: str):
        """
        Descomprime el archivo del driver e instala la impresora.
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Descomprimir el archivo ZIP
                with zipfile.ZipFile(compressed_driver_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Buscar el archivo .inf en el contenido descomprimido
                inf_files = [
                    os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith('.inf')
                ]
                if not inf_files:
                    raise Exception("No se encontró archivo .inf en el driver descomprimido.")

                inf_path = inf_files[0]  # Usar el primer archivo .inf encontrado

                # Instalar el driver según el sistema operativo
                if platform.system() == 'Windows':
                    return await self._install_windows(inf_path, printer_ip, manufacturer, model)
                else:
                    return await self._install_linux(inf_path, printer_ip, manufacturer, model)
        except Exception as e:
            logging.error(f"Error installing printer: {str(e)}")
            return {
                'success': False,
                'message': f"Error en instalación: {str(e)}"
            }
    async def _extract_driver(self, driver_data: bytes, temp_dir: str):
        """
        Descomprime el archivo de driver y busca el archivo .inf.
        """
        try:
            # Guardar el archivo comprimido en un directorio temporal
            zip_path = os.path.join(temp_dir, 'driver.zip')
            with open(zip_path, 'wb') as f:
                f.write(driver_data)

            # Descomprimir el archivo
            with zipfile.ZipFile(zip_path) as z:
                z.extractall(temp_dir)
                inf_files = [os.path.join(temp_dir, f) for f in z.namelist() if f.endswith('.inf')]
                if not inf_files:
                    raise Exception("No se encontró archivo .inf en el driver descomprimido.")
                return inf_files[0]  # Retornar la ruta del primer archivo .inf encontrado
        except zipfile.BadZipFile:
            raise Exception("El archivo proporcionado no es un archivo ZIP válido.")
        except Exception as e:
            raise Exception(f"Error al descomprimir el archivo: {str(e)}")

    async def _install_windows(self, inf_path: str, printer_ip: str, manufacturer: str, model: str):
        """
        Realiza la instalación en sistemas Windows.
        """
        try:
            # 1. Agregar el driver al sistema
            subprocess.run(['pnputil', '-i', '-a', inf_path], check=True, capture_output=True, text=True)

            # 2. Crear un puerto TCP/IP para la impresora
            port_name = f"IP_{printer_ip}"
            subprocess.run([
                'powershell',
                '-Command',
                f'Add-PrinterPort -Name "{port_name}" -PrinterHostAddress "{printer_ip}"'
            ], check=True, capture_output=True, text=True)

            # 3. Instalar la impresora
            printer_name = f"{manufacturer} {model}"
            subprocess.run([
                'powershell',
                '-Command',
                f'Add-Printer -Name "{printer_name}" -DriverName "{model}" -PortName "{port_name}"'
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

    async def _install_linux(self, inf_path: str, printer_ip: str, manufacturer: str, model: str):
        """
        Realiza la instalación en sistemas Linux usando CUPS.
        """
        try:
            # 1. Verificar si CUPS está instalado
            subprocess.run(['lpstat', '-v'], check=True, capture_output=True)

            # 2. Generar un nombre único para la impresora
            printer_name = f"{manufacturer}_{model}".replace(' ', '_')

            # 3. Verificar o convertir a un archivo .ppd si es necesario
            if inf_path.endswith('.ppd'):
                ppd_path = inf_path
            else:
                ppd_path = await self._convert_inf_to_ppd(inf_path)

            # 4. Agregar la impresora
            subprocess.run([
                'lpadmin',
                '-p', printer_name,
                '-v', f"socket://{printer_ip}",
                '-P', ppd_path,
                '-E'  # Habilitar la impresora
            ], check=True, capture_output=True, text=True)

            # 5. Establecer como impresora predeterminada
            subprocess.run(['lpoptions', '-d', printer_name], check=True, capture_output=True, text=True)

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
        Convierte un archivo .inf a .ppd (simplificado).
        """
        try:
            # Ruta al archivo .ppd
            ppd_dir = os.path.dirname(inf_path)
            ppd_path = os.path.join(ppd_dir, 'converted.ppd')

            # Verificar si existe un archivo .ppd relacionado
            existing_ppd = inf_path.replace('.inf', '.ppd')
            if os.path.exists(existing_ppd):
                return existing_ppd

            # Si no existe, lanzar error (falta lógica de conversión real)
            raise NotImplementedError("Conversión INF a PPD no implementada.")
        except Exception as e:
            raise Exception(f"Error en conversión INF a PPD: {str(e)}")

    async def uninstall(self, printer_name: str):
        """
        Desinstala una impresora previamente instalada.
        """
        try:
            if platform.system() == 'Windows':
                subprocess.run(['powershell', '-Command', f'Remove-Printer -Name "{printer_name}"'], check=True, capture_output=True, text=True)
            else:
                subprocess.run(['lpadmin', '-x', printer_name], check=True, capture_output=True, text=True)

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
        Lista las impresoras instaladas en el sistema.
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
                result = subprocess.run(['lpstat', '-p'], check=True, capture_output=True, text=True)
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
