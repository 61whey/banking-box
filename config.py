"""
Конфигурация банка
Команды кастомизируют эти параметры
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class BankConfig(BaseSettings):
    """Настройки банка"""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # 61whey: All default values removed for easy troubleshooting. Use .env file.
    # === ИДЕНТИФИКАЦИЯ БАНКА ===
    BANK_CODE: str
    BANK_NAME: str
    BANK_DESCRIPTION: str
    
    # === DATABASE ===
    DATABASE_URL: str
    
    # === SECURITY ===
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # === API ===
    API_VERSION: str
    API_BASE_PATH: str
    
    # === REGISTRY (для федеративной архитектуры) ===
    REGISTRY_URL: str
    PUBLIC_URL: str

    API_INTERNAL_PORT: int = 8000  # Default port for API
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    DEMO_CLIENT_PASSWORD: str

# Singleton instance
config = BankConfig()

