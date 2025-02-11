#agent\app\services\smb_service.py
import os
import subprocess
import win32net
import win32netcon
import win32security
import win32api
import win32con
import logging
import ctypes
from pathlib import Path
import wmi
import time

class SMBScannerService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scanner_user = "scanner_service"
        self.scanner_password = "Sc@nn3r2024#"
        self.scanner_folder = str(Path(os.path.expanduser("~/Desktop/scanner")))
        
    async def setup(self):
        """Configura todo el entorno necesario para el servicio de scanner"""
        try:
            # Verificar privilegios de administrador
            if not ctypes.windll.shell32.IsUserAnAdmin():
                self.logger.error("❌ Se requieren privilegios de administrador para configurar el servicio SMB")
                self.logger.info("Por favor, ejecute el programa como administrador")
                return False

            # Detectar nombre del grupo de administradores
            admin_group = self._get_admin_group_name()
            if not admin_group:
                self.logger.error("No se pudo determinar el nombre del grupo de administradores")
                return False

            # 1. Crear usuario local sin perfil
            self.logger.info("1/5: Creando usuario local...")
            self._create_local_user(admin_group)
            
            # 2. Activar características de Windows necesarias
            self.logger.info("2/5: Activando características de Windows...")
            self._enable_windows_features()
            
            # 3. Crear y configurar carpeta scanner
            self.logger.info("3/5: Configurando carpeta scanner...")
            self._setup_scanner_folder()
            
            # 4. Configurar compartición SMB
            self.logger.info("4/5: Configurando compartición SMB...")
            self._setup_smb_sharing()
            
            # 5. Configurar red para compartir
            self.logger.info("5/5: Configurando red...")
            self._configure_network_sharing()
            
            self.logger.info("✅ Configuración SMB completada exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en la configuración del servicio SMB: {e}")
            return False

    def _get_admin_group_name(self):
        """Detecta el nombre correcto del grupo de administradores según el idioma del sistema"""
        try:
            # Intentar nombres comunes según el idioma
            possible_names = ["Administrators", "Administradores", "Administrateurs"]
            
            for group_name in possible_names:
                try:
                    subprocess.run(
                        ['net', 'localgroup', group_name],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    self.logger.info(f"Grupo de administradores detectado: {group_name}")
                    return group_name
                except subprocess.CalledProcessError:
                    continue
                    
            # Si no se encuentra, intentar obtenerlo mediante WMI
            import wmi
            c = wmi.WMI()
            admin_group = c.Win32_Group(SID="S-1-5-32-544")[0]
            return admin_group.Name
            
        except Exception as e:
            self.logger.error(f"Error detectando grupo de administradores: {e}")
            return "Administrators"  # valor por defecto

    def _create_local_user(self, admin_group):
        """Crea usuario local administrador sin perfil"""
        try:
            # Preparar información del usuario
            user_info = {
                'name': self.scanner_user,
                'password': self.scanner_password,
                'priv': win32netcon.USER_PRIV_USER,
                'flags': win32netcon.UF_NORMAL_ACCOUNT | win32netcon.UF_DONT_EXPIRE_PASSWD,
                'script_path': '',
                'home_dir': ''
            }

            try:
                # Intentar crear el usuario
                win32net.NetUserAdd(None, 1, user_info)
                self.logger.info(f"Usuario {self.scanner_user} creado exitosamente")
                
                # Agregar al grupo de administradores usando el nombre detectado
                try:
                    subprocess.run(
                        ['net', 'localgroup', admin_group, self.scanner_user, '/add'],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    self.logger.info(f"Usuario {self.scanner_user} agregado al grupo {admin_group}")
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"Error agregando usuario a {admin_group}: {e.stdout} {e.stderr}")
                    raise
                    
            except win32net.error as e:
                if e.winerror == 2224:  # Usuario ya existe
                    self.logger.info(f"Usuario {self.scanner_user} ya existe")
                    return
                else:
                    self.logger.error(f"Error win32net: {e}")
                    raise

        except Exception as e:
            self.logger.error(f"Error creando usuario local: {e}")
            raise

    def _enable_windows_features(self):
        """Activa las características necesarias de Windows"""
        try:
            # Lista de comandos PowerShell para configuración
            commands = [
                # Configurar SMB
                ['powershell', 'Set-SmbServerConfiguration', '-EnableSMB2Protocol', '$true', '-Force'],
                ['powershell', 'Enable-WindowsOptionalFeature', '-Online', '-FeatureName', 'SMB1Protocol', '-All', '-NoRestart'],
                
                # Configurar firewall usando PowerShell en lugar de netsh
                ['powershell', 'Get-NetFirewallRule -DisplayGroup "File and Printer Sharing" | Set-NetFirewallRule -Enabled True -Profile Private'],
                ['powershell', 'Get-NetFirewallRule -DisplayGroup "Network Discovery" | Set-NetFirewallRule -Enabled True -Profile Private'],
                
                # Configurar servicios
                ['sc', 'config', 'lanmanworkstation', 'start=', 'auto'],
                ['sc', 'config', 'lanmanserver', 'start=', 'auto'],
                ['sc', 'start', 'lanmanworkstation'],
                ['sc', 'start', 'lanmanserver']
            ]
            
            reboot_required = False
            
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        check=False,  # No levantar excepción en error
                        capture_output=True,
                        text=True
                    )
                    
                    # Manejar códigos de salida específicos
                    if result.returncode == 3010:
                        self.logger.warning(f"Se requiere reinicio para {' '.join(cmd)}")
                        reboot_required = True
                    elif result.returncode != 0 and result.returncode != 1056:  # Ignorar error de servicio ya iniciado
                        self.logger.warning(f"Comando {' '.join(cmd)} falló con código {result.returncode}")
                        self.logger.debug(f"Salida: {result.stdout}\nError: {result.stderr}")
                    else:
                        self.logger.info(f"Comando ejecutado correctamente: {' '.join(cmd)}")
                            
                except subprocess.CalledProcessError as e:
                    self.logger.warning(f"Error ejecutando {' '.join(cmd)}: {e}")
                    continue
                        
            if reboot_required:
                self.logger.warning("⚠️ Se requiere reiniciar Windows para completar la configuración")
                    
            return True
                        
        except Exception as e:
            self.logger.error(f"Error activando características de Windows: {e}")
            raise

    def _setup_scanner_folder(self):
        """Configura la carpeta para escaneos"""
        try:
            # Crear carpeta si no existe
            os.makedirs(self.scanner_folder, exist_ok=True)
            
            # Obtener SID del usuario scanner
            scanner_sid = win32security.LookupAccountName(None, self.scanner_user)[0]
            
            # Obtener DACL actual
            security = win32security.GetFileSecurity(
                self.scanner_folder, 
                win32security.DACL_SECURITY_INFORMATION
            )
            dacl = security.GetSecurityDescriptorDacl()
            
            # Agregar permisos completos para el usuario scanner
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                win32con.GENERIC_ALL,
                scanner_sid
            )
            
            # Aplicar nueva DACL
            security.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                self.scanner_folder,
                win32security.DACL_SECURITY_INFORMATION,
                security
            )
            
        except Exception as e:
            self.logger.error(f"Error configurando carpeta scanner: {e}")
            raise

    def _setup_smb_sharing(self):
        """Configura compartición SMB de la carpeta scanner"""
        try:
            share_name = "Scanner"
            
            # 1. Asegurarse que la carpeta existe
            os.makedirs(self.scanner_folder, exist_ok=True)
            
            # 2. Eliminar compartición existente
            subprocess.run(['net', 'share', f'{share_name} /delete'], check=False, capture_output=True)
            time.sleep(1)
            
            # 3. Establecer permisos NTFS usando icacls
            icacls_commands = [
                f'icacls "{self.scanner_folder}" /reset',
                f'icacls "{self.scanner_folder}" /inheritance:r',
                f'icacls "{self.scanner_folder}" /grant:r "{self.scanner_user}":(OI)(CI)F',
                f'icacls "{self.scanner_folder}" /grant:r Everyone:(OI)(CI)(M)'
            ]
            
            for cmd in icacls_commands:
                subprocess.run(cmd, shell=True, check=True)
                
            self.logger.info("Permisos NTFS configurados con icacls")
            
            # 4. Crear compartición usando PowerShell (manera más limpia)
            ps_command = f'''
            $ShareName = "{share_name}"
            $Path = "{self.scanner_folder}"
            
            # Crear compartición nueva
            if (Get-SmbShare -Name $ShareName -ErrorAction SilentlyContinue) {{
                Remove-SmbShare -Name $ShareName -Force
            }}
            
            # Crear nueva compartición con permisos básicos
            New-SmbShare -Name $ShareName -Path $Path -FullAccess "{self.scanner_user}" -ChangeAccess "Everyone"
            
            # Mostrar permisos configurados
            Get-SmbShareAccess -Name $ShareName | Format-Table -AutoSize
            '''
            
            subprocess.run(['powershell', '-Command', ps_command], check=True)
            
            self.logger.info("✅ Configuración de compartición y permisos completada")
            return True
                
        except Exception as e:
            self.logger.error(f"Error configurando compartición SMB: {e}")
            if hasattr(e, 'output'):
                self.logger.error(f"Detalles: {e.output}")
            raise

    def _configure_network_sharing(self):
        """Configura las opciones de red y compartición para cualquier idioma de Windows"""
        try:
            ps_commands = [
                '''
                # Función para configurar el registro
                function Set-RegistryNetwork {
                    param(
                        [string]$Path,
                        [string]$Name,
                        [string]$Value,
                        [string]$Type = "DWord"
                    )
                    
                    if (-not (Test-Path $Path)) {
                        New-Item -Path $Path -Force | Out-Null
                    }
                    Set-ItemProperty -Path $Path -Name $Name -Value $Value -Type $Type -Force
                }

                # Configurar red como privada
                Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private

                # Activar descubrimiento de red y uso compartido para red privada
                $networkConfig = @{
                    # Activar descubrimiento de red
                    "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced\\Folder\\NetSharing" = @{
                        "DiscoveryState" = 1
                    }
                    
                    # Activar uso compartido de archivos
                    "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced\\Folder\\Sharing" = @{
                        "SharingState" = 1
                    }
                    
                    # Configurar seguridad y cifrado
                    "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\LanmanServer\\Parameters" = @{
                        "EnableFileSharing" = 1
                        "EnableNetworkDiscovery" = 1
                        "EnableSecuritySignature" = 1
                        "RequireSecuritySignature" = 1
                        "EnableAuthenticateUserSharing" = 1
                        "AutoShareServer" = 1
                        "AutoShareWks" = 1
                    }
                    
                    # Configurar detección automática
                    "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\NcdAutoSetup\\Private" = @{
                        "AutoSetup" = 1
                    }
                }

                # Aplicar configuraciones
                foreach ($path in $networkConfig.Keys) {
                    foreach ($setting in $networkConfig[$path].GetEnumerator()) {
                        Set-RegistryNetwork -Path $path -Name $setting.Key -Value $setting.Value
                    }
                }

                # Activar reglas de firewall específicas
                $rules = @(
                    "Network Discovery (NB-Name-In)",
                    "Network Discovery (NB-Datagram-In)",
                    "Network Discovery (WSD-In)",
                    "File and Printer Sharing (SMB-In)",
                    "File and Printer Sharing (NB-Session-In)"
                )

                foreach ($rule in $rules) {
                    Get-NetFirewallRule -DisplayName $rule -ErrorAction SilentlyContinue | 
                    Set-NetFirewallRule -Profile Private -Enabled True -ErrorAction SilentlyContinue
                }

                # Desactivar en redes públicas
                foreach ($rule in $rules) {
                    Get-NetFirewallRule -DisplayName $rule -ErrorAction SilentlyContinue | 
                    Set-NetFirewallRule -Profile Public -Enabled False -ErrorAction SilentlyContinue
                }

                # Activar opciones de uso compartido avanzado
                Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "EnableLinkedConnections" -Value 1 -Type DWord -Force
                Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" -Name "SharingWizardOn" -Value 0 -Type DWord -Force

                # Reiniciar servicios de red
                Restart-Service -Name "LanmanServer" -Force -ErrorAction SilentlyContinue
                '''
            ]
            
            # Ejecutar comandos PowerShell
            for cmd in ps_commands:
                try:
                    result = subprocess.run(
                        ['powershell', '-Command', cmd],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    self.logger.info(f"Configuración de red ejecutada correctamente")
                except subprocess.CalledProcessError as e:
                    self.logger.warning(f"Error en comando de red: {e.output}")
                    continue

            # Servicios esenciales (los nombres son constantes en todos los idiomas)
            services = {
                'lanmanworkstation': 'Workstation',
                'lanmanserver': 'Server',
                'lmhosts': 'TCP/IP NetBIOS Helper',
                'upnphost': 'UPnP Device Host',
                'SSDPSRV': 'SSDP Discovery',
                'fdrespub': 'Function Discovery Resource Publication',
                'WinRM': 'Windows Remote Management',
                'iphlpsvc': 'IP Helper',  # Necesario para UPnP
                'FDResPub': 'Function Discovery Resource Publication'
            }
            
            for service, display_name in services.items():
                try:
                    subprocess.run(['sc', 'config', service, 'start=', 'auto'], check=True)
                    try:
                        subprocess.run(['net', 'start', service], check=False)
                    except:
                        pass
                    self.logger.info(f"Servicio {display_name} configurado correctamente")
                except subprocess.CalledProcessError as e:
                    if e.returncode != 1056:
                        self.logger.warning(f"Error configurando servicio {display_name}: {e}")
                    
            return True
                    
        except Exception as e:
            self.logger.error(f"Error en configuración de red: {e}")
            raise