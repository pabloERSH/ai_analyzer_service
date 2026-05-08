from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Настройки приложения с загрузкой из .env файла"""
    
    # Основные настройки
    PROJECT_NAME: str = Field(default="AI Analyzer Service")
    VERSION: str = Field(default="0.1.0")
    DEBUG: bool = Field(default=False)
    
    # База данных
    DATABASE_URL: str = Field(..., description="URL подключения к PostgreSQL")
    
    # Redis для Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # Внешние сервисы
    DIARY_SERVICE_URL: str = Field(
        default="http://localhost:8001/api/v1",
        description="URL Diary Service"
    )
    
    # JWT настройки (должны совпадать с Auth Service!)
    JWT_SECRET_KEY: str = Field(
        ...,
        description="Секретный ключ для проверки JWT (такой же как в Auth Service)"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Алгоритм JWT"
    )
    
    # GigaChat API
    GIGACHAT_API_KEY: str = Field(default="")
    GIGACHAT_CLIENT_ID: str = Field(default="")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
