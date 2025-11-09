"""
Конфигурация банка
Команды кастомизируют эти параметры
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class BankConfig(BaseSettings):
    """Настройки банка"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
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
    
    # === CACHE ===
    REDIS_URL: str = "redis://localhost:6379"
    
    # Поля, используемые только в docker-compose, но не в приложении
    # Добавлены для избежания ошибок валидации
    TEAM_CLIENT_ID: Optional[str] = None
    TEAM_CLIENT_SECRET: Optional[str] = None
    POSTGRES_DATA_DIR: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_EXTERNAL_PORT: Optional[str] = None
    API_EXTERNAL_PORT: Optional[str] = None

# Singleton instance
config = BankConfig()

