import json
import asyncio
import logging
from app.tasks.celery_app import celery_app
from app.api.services.diary import DiaryServiceClient, InsufficientDataError
from app.api.services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Запускает async функцию в синхронном контексте Celery."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    try:
        return loop.run_until_complete(coro)
    finally:
        if not loop.is_running():
            loop.close()


@celery_app.task(bind=True, name="analyze_user_data")
def analyze_user_data_task(self, token: str, period_days: int = 7):
    """
    Celery задача: получает данные из Diary, отправляет в GigaChat, возвращает результат.
    Сохраняет в БД и кэш через синхронный движок.
    """
    logger.info(f"Celery task started: {self.request.id}, period_days={period_days}")

    try:
        # Шаг 1: получаем отчёт из Diary Service
        diary_client = DiaryServiceClient()

        try:
            report = _run_async(diary_client.get_weekly_report(
                token=token, period_days=period_days, include_previous_week=True
            ))
            logger.info("Report received from Diary Service")
        except InsufficientDataError as e:
            # Недостаточно данных — возвращаем информативный ответ
            return {
                "error": "insufficient_data",
                "message": e.message,
                "data_quality": e.data,
            }

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

        result = {"report": report, "analysis": analysis}

        # Шаг 5: сохраняем в БД (синхронно, без Redis для Celery)
        # Это делаем в API слое после получения результата

        return result

    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise


# Тест

@celery_app.task(bind=True, name="analyze_user_data_test")
def analyze_user_data_test_task(self, token: str, period_days: int = 7):
    """
    Тестовая Celery задача — без вызова GigaChat.
    Симулирует задержку 0.5-1.5 секунды как реальный запрос.
    """
    import time
    import random
    
    logger.info(f"Test Celery task started: {self.request.id}, period_days={period_days}")
    
    # Симулируем задержку как у реального запроса
    delay = random.uniform(0.5, 1.5)
    time.sleep(delay)
    
    try:
        # Получаем отчёт из Diary Service (реальный запрос)
        diary_client = DiaryServiceClient()
        report = _run_async(diary_client.get_weekly_report(
            token=token, period_days=period_days, include_previous_week=True
        ))
        logger.info(f"Report received from Diary Service (test mode)")
        
        # Мок-анализ вместо GigaChat
        analysis = {
            "title": f"Тестовый анализ (нагрузочное тестирование)",
            "nutrition_section": {
                "summary": "Мок-ответ для нагрузочного тестирования",
                "calories": "Тест",
                "protein": "Тест",
                "fats": "Тест",
                "carbs": "Тест",
                "consistency": "Тест",
                "trend_vs_previous": "Тест",
                "action_items": ["Тестовая рекомендация 1", "Тестовая рекомендация 2"],
            },
            "training_section": {
                "summary": "Мок-ответ",
                "frequency": "Тест",
                "volume": "Тест",
                "muscle_balance": "Тест",
                "alerts": "Тест",
                "action_items": ["Тестовая рекомендация"],
            },
            "overall_verdict": {
                "rating": 5,
                "text": f"Нагрузочное тестирование. Задержка: {delay:.1f}с",
            },
        }
        
        result = {
            "report": report,
            "analysis": analysis,
            "source": "mock_load_test",
            "delay": round(delay, 2),
        }
        
        logger.info(f"Test task completed: {self.request.id}, delay={delay:.1f}s")
        return result
        
    except Exception as e:
        logger.error(f"Test task failed: {e}")
        raise
    