import redis.asyncio as redis
from app.config import settings

_redis = None


def get_redis() -> redis.Redis:
    """Возвращает singleton экземпляр Redis клиента."""
    global _redis

    if _redis is None:
        redis_url = settings.REDIS_URL

        # Добавляем пароль если есть
        if settings.REDIS_PASSWORD:
            # Пересобираем URL с паролем
            if "redis://" in redis_url:
                redis_url = redis_url.replace(
                    "redis://", f"redis://:{settings.REDIS_PASSWORD}@"
                )

        _redis = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis
