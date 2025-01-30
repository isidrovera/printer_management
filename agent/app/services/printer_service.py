# agent/app/services/printer_service.py
import os
import tempfile
import zipfile
import time
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
                logging.info(f"Extrayendo drivers en: {temp_dir}")
                # Descomprimir el archivo ZIP
                with zipfile.ZipFile(compressed_driver_path, 'r') as zip_ref:
                    # Listar contenido antes de extraer
                    contents = zip_ref.namelist()
                    logging.debug(f"Contenido del ZIP: {contents}")
                    zip_ref.extractall(temp_dir)

                # Buscar archivos .inf de manera inteligente
                inf_files = []
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        # Normalizar el nombre del archivo a minúsculas
                        filename_lower = file.lower()
                        if filename_lower.endswith('.inf'):
                            full_path = os.path.join(root, file)
                            inf_files.append({
                                'path': full_path,
                                'name': file,
                                'size': os.path.getsize(full_path)
                            })
                            logging.info(f"Encontrado archivo INF: {file} ({os.path.getsize(full_path)} bytes)")

                if not inf_files:
                    logging.error("No se encontraron archivos .inf")
                    raise Exception("No se encontró archivo .inf en el driver descomprimido.")

                # Si hay múltiples archivos .inf, intentar encontrar el más relevante
                selected_inf = None
                if len(inf_files) > 1:
                    logging.info(f"Encontrados {len(inf_files)} archivos INF, buscando el más apropiado")
                    for inf in inf_files:
                        # Priorizar archivos que contengan el modelo en el nombre
                        if model.lower() in inf['name'].lower():
                            selected_inf = inf
                            logging.info(f"Seleccionado INF por coincidencia de modelo: {inf['name']}")
                            break

                    # Si no se encuentra por modelo, usar el más grande (suele ser el principal)
                    if not selected_inf:
                        selected_inf = max(inf_files, key=lambda x: x['size'])
                        logging.info(f"Seleccionado INF por tamaño: {selected_inf['name']}")
                else:
                    selected_inf = inf_files[0]
                    logging.info(f"Usando único archivo INF encontrado: {selected_inf['name']}")

                inf_path = selected_inf['path']
                logging.info(f"Usando archivo INF final: {inf_path}")

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
        try:
            logging.info(f"Instalando driver desde {inf_path}")
            
            # Obtener el nombre del driver del directorio (que es el nombre del archivo comprimido)
            dir_name = os.path.basename(os.path.dirname(inf_path))
            driver_name = dir_name  # No necesitamos quitar nada porque el directorio ya es el nombre sin extensión
            
            logging.info(f"Nombre del driver a usar: {driver_name}")

            # 1. Expandir archivos DLL
            driver_dir = os.path.dirname(inf_path)
            for file in os.listdir(driver_dir):
                if file.endswith('.dl_'):
                    original = os.path.join(driver_dir, file)
                    expanded = os.path.join(driver_dir, file[:-1])
                    subprocess.run(['expand', original, expanded], check=True)
                    logging.info(f"Expandido {file} a {file[:-1]}")

            # 2. Instalar el driver usando pnputil
            logging.info("Instalando driver usando pnputil...")
            subprocess.run(['pnputil', '-i', '-a', inf_path], check=True)

            # 3. Instalar específicamente como driver de impresora
            logging.info(f"Instalando driver de impresora: {driver_name}")
            try:
                subprocess.run([
                    'rundll32',
                    'printui.dll,PrintUIEntry',
                    '/ia',
                    '/m',
                    driver_name,
                    '/h',
                    'x64',
                    '/f',
                    inf_path
                ], check=True)
            except subprocess.CalledProcessError:
                logging.warning("Error en rundll32, continuando...")

            # 4. Verificar la instalación
            time.sleep(5)
            logging.info("Verificando instalación del driver...")
            result = subprocess.run([
                'powershell',
                '-Command',
                'Get-PrinterDriver | Select-Object Name, Manufacturer | Format-List'
            ], capture_output=True, text=True)
            logging.info(f"Drivers instalados:\n{result.stdout}")

            # 5. Verificar si el puerto existe
            port_name = f"IP_{printer_ip}"
            logging.info(f"Verificando puerto TCP/IP: {port_name}")
            check_port = subprocess.run([
                'powershell',
                '-Command',
                f'Get-PrinterPort -Name "{port_name}" 2>$null'
            ], capture_output=True, text=True)

            if "Name" not in check_port.stdout:
                logging.info("Creando nuevo puerto TCP/IP...")
                subprocess.run([
                    'powershell',
                    '-Command',
                    f'Add-PrinterPort -Name "{port_name}" -PrinterHostAddress "{printer_ip}"'
                ], check=True)
            else:
                logging.info("Puerto ya existe, usando puerto existente")

            # 6. Instalar la impresora
            printer_name = f"{manufacturer} {model}"
            logging.info(f"Instalando impresora {printer_name}...")
            subprocess.run([
                'powershell',
                '-Command',
                f'Add-Printer -Name "{printer_name}" -DriverName "{driver_name}" -PortName "{port_name}"'
            ], check=True)

            return {
                'success': True,
                'message': f'Impresora {printer_name} instalada correctamente'
            }
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error en instalación: {error_msg}")
            return {
                'success': False,
                'message': f"Error en instalación: {error_msg}"
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
