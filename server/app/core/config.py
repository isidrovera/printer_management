# server/app/core/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List, ClassVar

# Obtener la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # server/app/

class Settings(BaseSettings):
    # Configuración básica del proyecto
    PROJECT_NAME: str = "Printer Management System"
    DESCRIPTION: str = "Sistema de gestión de impresoras"
    API_V1_STR: str = "/api/v1"  # Añadida esta línea
    
    # Configuración de la base de datos y seguridad
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Configuración de almacenamiento de drivers
    DRIVERS_STORAGE_PATH: str = str(BASE_DIR / "storage" / "drivers")
    
    # Configuración del servidor
    SERVER_URL: str = "http://161.132.39.159:8000"
    SERVER_WS_URL: str = "ws://161.132.39.159:8000"
    
    # Configuración de logging como ClassVar para resolver el error de Pydantic
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
    
    # Headers de seguridad básicos
    SECURITY_HEADERS: Dict[str, str] = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block"
    }
    
    class Config:
        env_file = ".env"
        from_attributes = True  # Actualizado de orm_mode a from_attributes
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Asegurarse que el directorio de drivers existe
        os.makedirs(self.DRIVERS_STORAGE_PATH, exist_ok=True)
    
    def get_security_headers(self, is_websocket: bool = False) -> Dict[str, str]:
        """Obtiene los headers de seguridad apropiados."""
        headers = self.SECURITY_HEADERS.copy()
        if is_websocket:
            # Eliminar headers que no son necesarios para WebSocket
            headers.pop("X-Frame-Options", None)
        return headers

    def get_cors_origins(self) -> List[str]:
        if getattr(self, 'DEBUG', False):
            return ["*"]
        return [self.SERVER_URL]

settings = Settings()