import httpx
import logging
from app.config import settings
from app.api.services.gigachat_auth import get_access_token

logger = logging.getLogger(__name__)


async def send_message(system_prompt: str, user_message: str) -> str:
    """
    Отправляет сообщение в GigaChat и возвращает ответ.

    Точно как в примере из гайда:
    POST /api/v1/chat/completions
    {
      model: 'GigaChat:latest',
      messages: [...],
      temperature: 0.7,
      max_tokens: 1000,
    }

    Args:
        system_prompt: системный промпт (rules для модели)
        user_message: данные пользователя

    Returns:
        str: текст ответа модели
    """
    # Получаем токен (из кэша или новый)
    access_token = await get_access_token()

    url = settings.GIGACHAT_API_URL
    model = settings.GIGACHAT_MODEL
    temperature = settings.GIGACHAT_TEMPERATURE
    max_tokens = settings.GIGACHAT_MAX_TOKENS

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    logger.info(
        f"Sending to GigaChat: model={model}, temperature={temperature}, max_tokens={max_tokens}"
    )
    logger.debug(f"System prompt length: {len(system_prompt)} chars")
    logger.debug(f"User message length: {len(user_message)} chars")

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            url,
            headers=headers,
            json=body,
            timeout=120.0,
        )

        logger.info(f"GigaChat response: status={response.status_code}")

        if response.status_code != 200:
            logger.error(f"GigaChat error: {response.status_code} {response.text}")
            raise Exception(
                f"GigaChat API error: {response.status_code} {response.text}"
            )

        result = response.json()

        choices = result.get("choices", [])
        if not choices:
            logger.warning("No choices in response")
            return ""

        content = choices[0].get("message", {}).get("content", "")
        logger.info(f"Response received: {len(content)} chars")

        return content

def send_message_sync(system_prompt: str, user_message: str) -> str:
    """Синхронная обёртка для Celery"""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(send_message(system_prompt, user_message))
    finally:
        loop.close()

