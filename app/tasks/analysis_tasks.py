import json
import asyncio
import logging
from app.tasks.celery_app import celery_app
from app.api.services.diary import DiaryServiceClient
from app.api.services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="analyze_user_data")
def analyze_user_data_task(self, token: str, period_days: int = 7):
    """
    Celery задача: получает данные, отправляет в GigaChat, возвращает результат.
    Выполняется в фоне, не блокирует HTTP-запрос.
    """
    logger.info(f"Celery task started: {self.request.id}, period_days={period_days}")
    
    try:
        # Шаг 1: получаем отчёт из Diary Service
        diary_client = DiaryServiceClient()
        report = _run_async(diary_client.get_weekly_report(
            token=token, period_days=period_days, include_previous_week=True
        ))
        logger.info("Report received from Diary Service")
        
        # Шаг 2: формируем промпт
        prompt_builder = PromptBuilder()
        system_prompt = prompt_builder.SYSTEM_PROMPT
        user_prompt = prompt_builder.build_user_prompt(report)
        
        # Шаг 3: отправляем в GigaChat
        from app.api.services.gigachat_client import send_message
        llm_response = _run_async(send_message(system_prompt, user_prompt))
        logger.info(f"GigaChat response: {len(llm_response)} chars")
        
        # Шаг 4: парсим ответ
        cleaned = llm_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        try:
            analysis = json.loads(cleaned.strip())
        except json.JSONDecodeError:
            analysis = {"raw_response": llm_response}
        
        return {"report": report, "analysis": analysis}
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise


def _run_async(coro):
    """Запускает async функцию в синхронном контексте Celery"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        