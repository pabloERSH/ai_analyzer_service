from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения с загрузкой из .env файла"""

    # Основные настройки (имеют значения по умолчанию, можно не указывать в .env)
    PROJECT_NAME: str = Field(
        default="AI Analyzer Service", description="Название проекта"
    )
    VERSION: str = Field(default="0.1.0", description="Версия приложения")

    # База данных (обязательные поля, без значений по умолчанию)
    DATABASE_URL: str = Field(
        ...,  # ... означает обязательное поле
        description="URL подключения к PostgreSQL",
    )

    # Redis для Celery
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", description="URL подключения к Redis"
    )

    # Внешние сервисы
    DIARY_SERVICE_URL: str = Field(
        default="http://localhost:8001/api/v1", description="URL Diary Service"
    )
    AUTH_SERVICE_URL: str = Field(
        default="http://localhost:8000/api/v1", description="URL Auth Service"
    )

    # LLM API ключи
    GIGACHAT_API_KEY: str = Field(default="", description="API ключ GigaChat")
    GIGACHAT_CLIENT_ID: str = Field(default="", description="Client ID для GigaChat")

    # Настройки безопасности
    SECRET_KEY: str = Field(..., description="Секретный ключ для подписи JWT")
    JWT_ALGORITHM: str = Field(default="HS256", description="Алгоритм JWT")

    # Настройки окружения
    DEBUG: bool = Field(default=False, description="Режим отладки")
    ENVIRONMENT: str = Field(
        default="development", description="Окружение (development/staging/production)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True  # Учитываем регистр в именах переменных


# Создаём экземпляр настроек
settings = Settings()
