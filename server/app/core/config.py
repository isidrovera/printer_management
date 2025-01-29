# server/app/core/config.py
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# Obtener la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # server/app/
# Agregamos la configuración del SERVER_URL
SERVER_URL: str = "http://161.132.39.159:8000"  # Ajusta esta URL según tu servidor
class Settings(BaseSettings):
    PROJECT_NAME: str = "Printer Management System"
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Configuración de almacenamiento de drivers
    DRIVERS_STORAGE_PATH: str = str(BASE_DIR / "storage" / "drivers")
    
    class Config:
        env_file = ".env"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Asegurarse que el directorio de drivers existe
        os.makedirs(self.DRIVERS_STORAGE_PATH, exist_ok=True)

settings = Settings()