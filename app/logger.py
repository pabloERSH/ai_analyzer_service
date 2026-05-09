import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.config import settings

# Директория для логов
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Формат логов
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)


def setup_logging():
    """Настраивает корневой логгер"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Очищаем существующие обработчики
    root_logger.handlers.clear()

    # 1. Вывод в stdout (для docker logs)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    root_logger.addHandler(console_handler)

    # 2. Файл для всех логов с ротацией (10 МБ, 5 файлов)
    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # 3. Отдельный файл только для ошибок
    error_handler = RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    # Уменьшаем шум от сторонних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)

    root_logger.info("=" * 50)
    root_logger.info(f"AI Analyzer Service starting (debug={settings.DEBUG})")
    root_logger.info("=" * 50)
