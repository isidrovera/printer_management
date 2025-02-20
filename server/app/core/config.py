# server/app/core/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List, ClassVar

# Obtener la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Configuración básica del proyecto
    PROJECT_NAME: str = "Printer Management System"
    DESCRIPTION: str = "Sistema de gestión de impresoras"
    API_V1_STR: str = "/api/v1"
    
    # Configuración de la base de datos y seguridad
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Configuración de almacenamiento de drivers
    DRIVERS_STORAGE_PATH: str = str(BASE_DIR / "storage" / "drivers")
    
    # Configuración del servidor (actualizado a HTTPS)
    SERVER_URL: str = "https://copierconnectremote.com"  # Cambiado a HTTPS
    SERVER_WS_URL: str = "wss://copierconnectremote.com"  # Cambiado a WSS
    
    # Configuración de logging
    LOGGING_CONFIG: ClassVar[Dict[str, Any]] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": "INFO",
            }
        }
    }
    
    # Headers de seguridad
    SECURITY_HEADERS: Dict[str, str] = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"  # Añadido HSTS
    }
    
    class Config:
        env_file = ".env"
        from_attributes = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        os.makedirs(self.DRIVERS_STORAGE_PATH, exist_ok=True)
    
    def get_security_headers(self, is_websocket: bool = False) -> Dict[str, str]:
        headers = self.SECURITY_HEADERS.copy()
        if is_websocket:
            headers.pop("X-Frame-Options", None)
        return headers
    
    def get_cors_origins(self) -> List[str]:
        return [
            "https://copierconnectremote.com",
            "https://www.copierconnectremote.com"
        ]
    
    def get_api_url(self, path: str = "") -> str:
        """Obtiene la URL completa para la API, asegurando HTTPS"""
        return f"{self.SERVER_URL}{self.API_V1_STR}{path}"

settings = Settings()