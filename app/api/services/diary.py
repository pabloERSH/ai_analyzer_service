import httpx
from typing import Optional, Dict, Any
from datetime import date
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class DiaryServiceError(Exception):
    """Ошибка от Diary Service"""
    def __init__(self, message: str, status_code: int = 400, data: dict = None):
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(message)


class InsufficientDataError(DiaryServiceError):
    """Недостаточно данных для анализа"""
    pass


class DiaryServiceClient:
    def __init__(self):
        self.base_url = settings.DIARY_SERVICE_URL.rstrip('/')
    
    async def get_weekly_report(
        self,
        token: str,
        period_days: int = 7,
        end_date: Optional[date] = None,
        include_previous_week: bool = True,
        include_meals_detail: bool = False,
        include_exercises_detail: bool = False
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/profile/report/weekly/"
        
        params = {
            "period_days": period_days,
            "include_previous_week": str(include_previous_week).lower(),
            "include_meals_detail": str(include_meals_detail).lower(),
            "include_exercises_detail": str(include_exercises_detail).lower()
        }
        
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        logger.info(f"Requesting Diary Service: {url}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, params=params, headers=headers, timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                
                # Обрабатываем ошибки
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                
                if response.status_code == 400:
                    detail = error_data.get("detail", "")
                    
                    # Проверяем на недостаточность данных
                    if "Недостаточно данных" in str(detail) or "sufficient_data" in str(error_data):
                        data_quality = error_data.get("data_quality", {})
                        raise InsufficientDataError(
                            message=str(detail),
                            data={
                                "nutrition_days": data_quality.get("nutrition_days_count", 0),
                                "training_days": data_quality.get("training_days_count", 0),
                                "min_required": error_data.get("min_required_days", 3),
                                "hint": error_data.get("hint", ""),
                            }
                        )
                    
                    raise DiaryServiceError(
                        message=f"Ошибка валидации: {detail}",
                        status_code=400,
                        data=error_data,
                    )
                
                elif response.status_code == 401:
                    raise DiaryServiceError(
                        message="Ошибка авторизации в Diary Service",
                        status_code=401,
                    )
                elif response.status_code == 403:
                    raise DiaryServiceError(
                        message="Доступ запрещён",
                        status_code=403,
                    )
                else:
                    raise DiaryServiceError(
                        message=f"Ошибка Diary Service: {response.status_code}",
                        status_code=response.status_code,
                    )
                    
            except httpx.RequestError as e:
                raise DiaryServiceError(
                    message=f"Diary Service недоступен: {str(e)}",
                    status_code=503,
                )
                