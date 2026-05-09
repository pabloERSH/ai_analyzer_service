from typing import Dict, Any
from app.api.services.diary import DiaryServiceClient
from app.api.services.gigachat_client import send_message
from app.api.services.prompt_builder import PromptBuilder
import json
import logging

logger = logging.getLogger(__name__)


class AnalysisService:
    """Основной сервис для проведения анализа"""

    def __init__(self):
        self.diary_client = DiaryServiceClient()
        self.prompt_builder = PromptBuilder()

    async def analyze_user_data(
        self, token: str, period_days: int = 7
    ) -> Dict[str, Any]:
        """
        Полный цикл анализа:
        1. Получает данные из Diary Service
        2. Формирует промпт
        3. Отправляет в GigaChat
        4. Парсит ответ
        """
        logger.info(f"Starting analysis, period_days={period_days}")

        # 1. Получаем отчёт из Diary Service
        report = await self.diary_client.get_weekly_report(
            token=token, period_days=period_days, include_previous_week=True
        )
        logger.info("Report received from Diary Service")

        # 2. Формируем промпт
        system_prompt = self.prompt_builder.SYSTEM_PROMPT
        user_prompt = self.prompt_builder.build_user_prompt(report)

        # 3. Отправляем в GigaChat
        llm_response = await send_message(system_prompt, user_prompt)
        logger.info(f"GigaChat response received: {len(llm_response)} chars")

        # 4. Парсим ответ
        try:
            analysis = _parse_llm_response(llm_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {e}")
            analysis = {
                "title": "Ошибка обработки ответа",
                "raw_response": llm_response,
            }

        return {"report": report, "analysis": analysis}


def _parse_llm_response(response: str) -> dict:
    """Очищает ответ от markdown-обёрток и парсит JSON."""
    cleaned = response.strip()

    # Убираем ```json ... ``` или ``` ... ```
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    cleaned = cleaned.strip()
    return json.loads(cleaned)
