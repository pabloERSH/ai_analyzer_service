import redis.asyncio as redis
from app.config import settings

_redis = None


def get_redis() -> redis.Redis:
    global _redis

    if _redis is None:
        redis_url = settings.REDIS_URL

        _redis = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    return _redis
