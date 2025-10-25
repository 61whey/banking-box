"""
Конфигурация банка
Команды кастомизируют эти параметры
"""
from pydantic_settings import BaseSettings


class BankConfig(BaseSettings):
    """Настройки банка"""
    
    # === ИДЕНТИФИКАЦИЯ БАНКА (КАСТОМИЗИРУЙ!) ===
    BANK_CODE: str = "vbank"
    BANK_NAME: str = "Virtual Bank"
    BANK_DESCRIPTION: str = "Виртуальный банк - эмуляция от организаторов"
    
    # === DATABASE ===
    DATABASE_URL: str = "postgresql://hackapi_user:hackapi_pass@localhost:5432/vbank_db"
    
    # === SECURITY ===
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # === API ===
    API_VERSION: str = "2.1"
    API_BASE_PATH: str = ""
    
    # === REGISTRY (для федеративной архитектуры) ===
    REGISTRY_URL: str = "http://localhost:3000"
    PUBLIC_URL: str = "http://localhost:8001"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
config = BankConfig()

