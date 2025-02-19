# server/app/core/config.py
# server/app/core/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
import logging.config

# Obtener el directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Configuración básica del proyecto
    PROJECT_NAME: str = "Copier Connect Remote"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Sistema de gestión remota de impresoras"
    
    # Configuración de la base de datos
    DATABASE_URL: str
    DATABASE_CONNECT_DICT: Dict[str, Any] = {}
    
    # Configuración de seguridad
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Configuración de almacenamiento
    DRIVERS_STORAGE_PATH: str = str(BASE_DIR / "storage" / "drivers")
    LOGS_STORAGE_PATH: str = str(BASE_DIR / "storage" / "logs")
    TEMP_STORAGE_PATH: str = str(BASE_DIR / "storage" / "temp")
    
    # Configuración del servidor
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DOMAIN: str = "copierconnectremote.com"
    
    # Configuración de proxy y seguridad
    PROXY_PREFIX: str = ""  # Por si Nginx añade un prefijo
    BEHIND_PROXY: bool = True
    TRUST_PROXY_HEADERS: bool = True
    
    # Configuración CORS - Permitir Cloudflare
    BACKEND_CORS_ORIGINS: List[str] = [
        f"https://{DOMAIN}",
        f"https://www.{DOMAIN}",
        "http://localhost:8000",
        "http://localhost:3000"
    ]
    
    # Headers de seguridad por defecto
    SECURITY_HEADERS: Dict[str, str] = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": (
            "default-src 'self' https: wss:; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
            "connect-src 'self' https: wss:;"
        )
    }
    
    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "access": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "default",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(BASE_DIR / "storage" / "logs" / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "access_file": {
                "formatter": "access",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(BASE_DIR / "storage" / "logs" / "access.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {  # Raíz
                "handlers": ["console", "file"],
                "level": "INFO",
            },
            "uvicorn.access": {
                "handlers": ["access_file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    
    # Configuración de archivos
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_UPLOAD_EXTENSIONS: set = {'.exe', '.msi', '.zip', '.pdf'}
    
    @property
    def SERVER_URL(self) -> str:
        """URL base del servidor."""
        if self.DEBUG:
            return f"http://{self.HOST}:{self.PORT}"
        return f"https://{self.DOMAIN}"
    
    @property
    def SERVER_WS_URL(self) -> str:
        """URL base para WebSocket."""
        if self.DEBUG:
            return f"ws://{self.HOST}:{self.PORT}"
        return f"wss://{self.DOMAIN}"
    
    @property
    def WS_PATH(self) -> str:
        return f"{self.API_V1_STR}/ws/status"
    
    def get_cors_origins(self) -> List[str]:
        """Obtiene los orígenes permitidos para CORS."""
        if self.DEBUG:
            return ["*"]
        return self.BACKEND_CORS_ORIGINS
    
    def get_security_headers(self, is_websocket: bool = False) -> Dict[str, str]:
        """Obtiene los headers de seguridad."""
        headers = self.SECURITY_HEADERS.copy()
        if is_websocket:
            headers.pop("Content-Security-Policy", None)
        return headers
    
    def get_ws_url(self) -> str:
        """Obtiene la URL completa para WebSocket."""
        return f"{self.SERVER_WS_URL}{self.WS_PATH}"
    
    def get_api_url(self, path: str = "") -> str:
        """Obtiene la URL completa para la API."""
        return f"{self.SERVER_URL}{self.API_V1_STR}{path}"
    
    def validate_upload_file(self, filename: str) -> bool:
        """Valida si un archivo puede ser subido al sistema."""
        return any(filename.lower().endswith(ext) for ext in self.ALLOWED_UPLOAD_EXTENSIONS)
    
    def get_file_path(self, filename: str, storage_type: str = "drivers") -> Path:
        """Obtiene la ruta completa para un archivo."""
        storage_map = {
            "drivers": self.DRIVERS_STORAGE_PATH,
            "logs": self.LOGS_STORAGE_PATH,
            "temp": self.TEMP_STORAGE_PATH
        }
        base_path = storage_map.get(storage_type, self.TEMP_STORAGE_PATH)
        return Path(base_path) / filename

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

# Instancia global de configuración
settings = Settings()