# server/app/core/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# Obtener la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # server/app/

class Settings(BaseSettings):
    PROJECT_NAME: str = "Printer Management System"
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # 🔹 Agregar estas líneas faltantes
    JWT_ALGORITHM: str = "HS256"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Opcional, pero se usa en create_refresh_token()
    
    # Configuración de almacenamiento de drivers
    DRIVERS_STORAGE_PATH: str = str(BASE_DIR / "storage" / "drivers")
    
    # Configuración del servidor
    SERVER_URL: str = "http://161.132.39.159:8000"  # Movido dentro de la clase
    SERVER_WS_URL: str = "ws://161.132.39.159:8000" 
    
    class Config:
        env_file = ".env"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Asegurarse que el directorio de drivers existe
        os.makedirs(self.DRIVERS_STORAGE_PATH, exist_ok=True)

settings = Settings()