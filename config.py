"""
Конфигурация банка
"""
from pydantic_settings import BaseSettings


class BankConfig(BaseSettings):
    """Настройки банка"""
    
    # === ИДЕНТИФИКАЦИЯ БАНКА (КАСТОМИЗИРУЙ!) ===
    BANK_CODE: str = "convolute"
    BANK_NAME: str = "Convolute"
    BANK_DESCRIPTION: str = "Convolute - сверточно-разверточный банк"
    
    # === DATABASE ===
    DATABASE_URL: str #= "postgresql://postgres:postgres@localhost:5432/local_convolute"
    
    # === SECURITY ===
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # === API ===
    API_VERSION: str = "2.1"
    API_BASE_PATH: str = ""
    
    # === REGISTRY (для федеративной архитектуры) ===
    # Connection to the Directory Service - a centralized registry
    # More info in doc/README.org.md
    REGISTRY_URL: str = "http://localhost:3000"
    PUBLIC_URL: str = "http://localhost:8001"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
config = BankConfig()

