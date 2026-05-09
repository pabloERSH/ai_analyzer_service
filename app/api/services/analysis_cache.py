import json
import logging
from app.api.services.redis_client import get_redis

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # 1 час


def _cache_key(telegram_id: int, period_start: str, period_end: str) -> str:
    return f"analysis:{telegram_id}:{period_start}:{period_end}"


async def get_cached(
    telegram_id: int, period_start: str, period_end: str
) -> dict | None:
    """Проверяет кэш Redis. Возвращает результат или None."""
    redis = get_redis()
    key = _cache_key(telegram_id, period_start, period_end)

    cached = await redis.get(key)
    if cached:
        logger.info(f"Cache hit: {key}")
        return json.loads(cached)

    logger.info(f"Cache miss: {key}")
    return None


async def set_cached(
    telegram_id: int, period_start: str, period_end: str, result: dict
):
    """Сохраняет результат в Redis на 1 час."""
    redis = get_redis()
    key = _cache_key(telegram_id, period_start, period_end)

    await redis.set(key, json.dumps(result, ensure_ascii=False), ex=CACHE_TTL)
    logger.info(f"Cached: {key}")
