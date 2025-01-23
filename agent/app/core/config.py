# agent/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVER_URL: str
    CLIENT_TOKEN: str
    AGENT_TOKEN: str | None = None
    
    class Config:
        env_file = ".env"

settings = Settings()