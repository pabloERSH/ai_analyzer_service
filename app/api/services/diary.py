import httpx
from typing import Optional, Dict, Any
from datetime import date
from app.config import settings


class DiaryServiceClient:
    """Клиент для получения агрегированных отчётов из Diary Service"""

    def __init__(self):
        self.base_url = settings.DIARY_SERVICE_URL.rstrip("/")

    async def get_weekly_report(
        self,
        token: str,
        period_days: int = 7,
        end_date: Optional[date] = None,
        include_previous_week: bool = True,
        include_meals_detail: bool = False,
        include_exercises_detail: bool = False,
    ) -> Dict[str, Any]:
        """
        Получает агрегированный недельный отчёт из Diary Service.

        Args:
            token: JWT токен для авторизации
            period_days: Глубина анализа в днях (3-31)
            end_date: Последний день периода (YYYY-MM-DD)
            include_previous_week: Сравнение с предыдущим периодом
            include_meals_detail: Добавить детализацию приёмов пищи
            include_exercises_detail: Добавить детализацию упражнений

        Returns:
            JSON-отчёт для последующей передачи в LLM

        Raises:
            httpx.HTTPError: При ошибках сети или HTTP
        """
        # Формируем URL
        url = f"{self.base_url}/profile/report/weekly/"

        # Параметры запроса
        params = {
            "period_days": period_days,
            "include_previous_week": str(include_previous_week).lower(),
            "include_meals_detail": str(include_meals_detail).lower(),
            "include_exercises_detail": str(include_exercises_detail).lower(),
        }

        if end_date:
            params["end_date"] = end_date.isoformat()

        # Заголовки с токеном авторизации
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, params=params, headers=headers, timeout=30.0
                )

                # Проверяем статус ответа
                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as e:
                # Обрабатываем специфические ошибки от Diary Service
                if e.response.status_code == 400:
                    error_data = e.response.json()
                    raise Exception(f"Diary Service validation error: {error_data}")
                elif e.response.status_code == 401:
                    raise Exception("Authentication failed with Diary Service")
                elif e.response.status_code == 403:
                    raise Exception("Access denied to Diary Service")
                else:
                    raise Exception(
                        f"Diary Service error: {e.response.status_code} - {e.response.text}"
                    )

            except httpx.RequestError as e:
                raise Exception(f"Failed to connect to Diary Service: {str(e)}")
