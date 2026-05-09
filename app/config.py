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
    REDIS_URL: str = Field(...)
    REDIS_PASSWORD: str = Field(...)

    # Внешние сервисы
    DIARY_SERVICE_URL: str = Field(
        default="http://localhost:8001/api/v1", description="URL Diary Service"
    )

    # JWT настройки (должны совпадать с Auth Service!)
    JWT_SECRET_KEY: str = Field(
        ..., description="Секретный ключ для проверки JWT (такой же как в Auth Service)"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="Алгоритм JWT")

    # GigaChat API
    GIGACHAT_CLIENT_ID: str = Field(...)
    GIGACHAT_API_KEY: str = Field(...)
    GIGACHAT_AUTH_URL: str = Field(
        default="https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    )
    GIGACHAT_API_URL: str = Field(
        default="https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    )
    GIGACHAT_MODEL: str = Field(default="GigaChat:latest")
    GIGACHAT_TEMPERATURE: float = Field(default=0.7)
    GIGACHAT_MAX_TOKENS: int = Field(default=3000)
    GIGACHAT_SCOPE: str = Field(default="GIGACHAT_API_PERS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
