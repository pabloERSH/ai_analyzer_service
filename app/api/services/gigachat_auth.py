import httpx
import uuid
import logging
from datetime import datetime, timezone
from app.config import settings

logger = logging.getLogger(__name__)

_cached_token: str | None = None
_token_expires_at: float = 0


async def get_access_token() -> str:
    global _cached_token, _token_expires_at

    now = datetime.now(timezone.utc).timestamp()

    if _cached_token and _token_expires_at > now + 60:
        logger.debug("Using cached access token")
        return _cached_token

    logger.info("Requesting new access token")

    client_id = settings.GIGACHAT_CLIENT_ID.strip()
    client_secret = settings.GIGACHAT_API_KEY.strip()

    rq_uid = str(uuid.uuid4())

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Authorization": f"Basic {client_secret}",
        "RqUID": rq_uid,
    }

    body = {"scope": settings.GIGACHAT_SCOPE}

    logger.info(f"Auth request: client_id={client_id}, scope={settings.GIGACHAT_SCOPE}")

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            settings.GIGACHAT_AUTH_URL,
            headers=headers,
            data=body,
            timeout=30.0,
        )

        if response.status_code != 200:
            raise Exception(
                f"GigaChat auth failed: {response.status_code} - {response.text}"
            )

        data = response.json()

        _cached_token = data["access_token"]
        # expires_at в миллисекундах, переводим в секунды
        _token_expires_at = data["expires_at"] / 1000.0

        logger.info(
            f"Token obtained, expires_at={datetime.fromtimestamp(_token_expires_at).isoformat()}"
        )
        return _cached_token
