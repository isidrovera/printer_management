# server/app/core/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Obtener el directorio base del proyecto (raíz)
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # server/

# Directorio raíz del proyecto (un nivel arriba)
PROJECT_ROOT = BASE_DIR.parent  # printer_management/

# Intenta varias ubicaciones posibles para el archivo .env
locations_to_try = [
    str(BASE_DIR / ".env"),                # server/.env
    str(PROJECT_ROOT / ".env"),            # printer_management/.env
    str(PROJECT_ROOT / "server" / ".env"), # printer_management/server/.env
    str(Path.cwd() / ".env"),              # Directorio de trabajo actual/.env
    str(Path.cwd() / "server" / ".env")    # Directorio de trabajo actual/server/.env
]

# Buscar y cargar .env de cualquiera de las ubicaciones
env_loaded = False
env_file_path = None

for loc in locations_to_try:
    if os.path.exists(loc):
        print(f"✅ Archivo .env encontrado en {loc}")
        load_dotenv(loc)
        env_file_path = loc
        env_loaded = True
        break

if not env_loaded:
    print(f"⚠️ Archivo .env no encontrado. Ubicaciones probadas: {locations_to_try}")
    # Valor predeterminado para evitar errores
    env_file_path = str(BASE_DIR / ".env")

class Settings(BaseSettings):
    # Configuración básica del proyecto
    PROJECT_NAME: str = "Copier Connect Remote"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sistema de gestión remota de impresoras"

    # Configuración de la base de datos
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost/printer_management"
    DATABASE_CONNECT_DICT: Dict[str, Any] = {}

    # Configuración de seguridad
    SECRET_KEY: str = "tu_clave_secreta_aqui"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas en lugar de 60 minutos
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Configuración de almacenamiento
    DRIVERS_STORAGE_PATH: str = str(BASE_DIR / "storage" / "drivers")
    LOGS_STORAGE_PATH: str = str(BASE_DIR / "storage" / "logs")
    TEMP_STORAGE_PATH: str = str(BASE_DIR / "storage" / "temp")

    # Configuración del servidor
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # URLs base del servidor
    @property
    def SERVER_URL(self) -> str:
        return "https://copierconnectremote.com"

    @property
    def SERVER_WS_URL(self) -> str:
        return "wss://copierconnectremote.com"

    @property
    def WS_PATH(self) -> str:
        return "/api/v1/ws/status"

    # Configuración de correo (opcional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configuración de CORS
    BACKEND_CORS_ORIGINS: list = ["*"]

    # Configuración de archivos
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_UPLOAD_EXTENSIONS: set = {'.exe', '.msi', '.zip', '.pdf'}

    # Métodos auxiliares
    def get_ws_url(self) -> str:
        """Obtiene la URL completa para WebSocket"""
        return f"{self.SERVER_WS_URL}{self.WS_PATH}"

    def get_api_url(self, path: str = "") -> str:
        """Obtiene la URL completa para la API"""
        return f"{self.SERVER_URL}{self.API_V1_STR}{path}"

    class Config:
        env_file = env_file_path  # Usa la ruta encontrada
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Crear directorios necesarios
        for path in [
            self.DRIVERS_STORAGE_PATH,
            self.LOGS_STORAGE_PATH,
            self.TEMP_STORAGE_PATH
        ]:
            os.makedirs(path, exist_ok=True)

        # Configurar conexión a la base de datos
        if self.DATABASE_URL.startswith("postgresql"):
            self.DATABASE_CONNECT_DICT = {
                "sslmode": "require" if not self.DEBUG else "disable"
            }

    def validate_upload_file(self, filename: str) -> bool:
        """Valida si un archivo puede ser subido al sistema"""
        return any(filename.lower().endswith(ext) for ext in self.ALLOWED_UPLOAD_EXTENSIONS)

    def get_file_path(self, filename: str, storage_type: str = "drivers") -> Path:
        """Obtiene la ruta completa para un archivo"""
        storage_map = {
            "drivers": self.DRIVERS_STORAGE_PATH,
            "logs": self.LOGS_STORAGE_PATH,
            "temp": self.TEMP_STORAGE_PATH
        }
        base_path = storage_map.get(storage_type, self.TEMP_STORAGE_PATH)
        return Path(base_path) / filename

# Instancia global de configuración
settings = Settings()