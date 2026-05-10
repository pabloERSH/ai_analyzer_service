from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional


class AnalysisStatus(str, Enum):
    """Статусы задачи анализа"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    INSUFFICIENT_DATA = "insufficient_data" 


class AnalysisRequest(BaseModel):
    """Запрос на создание анализа"""

    period_days: int = Field(
        default=7, ge=3, le=31, description="Период анализа в днях (3-31)"
    )
    analysis_type: str = Field(
        default="full",
        pattern="^(full|nutrition|training)$",
        description="Тип анализа: full, nutrition, training",
    )

    class Config:
        json_schema_extra = {"example": {"period_days": 7, "analysis_type": "full"}}


class AnalysisResponse(BaseModel):
    """Ответ с информацией о задаче анализа"""

    task_id: str = Field(..., description="Уникальный идентификатор задачи")
    status: AnalysisStatus = Field(..., description="Текущий статус задачи")
    telegram_id: int = Field(..., description="Telegram ID пользователя")
    period_days: int = Field(..., description="Период анализа в днях")
    analysis_type: str = Field(..., description="Тип анализа")
    result: Optional[dict] = Field(None, description="Результат анализа (если готов)")
    created_at: datetime = Field(..., description="Время создания задачи")
    completed_at: Optional[datetime] = Field(
        None, description="Время завершения задачи"
    )
    error_message: Optional[str] = Field(
        None, description="Сообщение об ошибке (если есть)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "telegram_id": 123456789,
                "period_days": 7,
                "analysis_type": "full",
                "result": {
                    "period": {"start": "2026-05-01", "end": "2026-05-08", "days": 7},
                    "summary": "🥗 Питание: 6/7 дней, в среднем 2300 ккал/день...",
                },
                "created_at": "2026-05-08T12:00:00.000000",
                "completed_at": "2026-05-08T12:00:01.000000",
                "error_message": None,
            }
        }


class TaskStatus(BaseModel):
    """Статус задачи для polling"""

    task_id: str = Field(..., description="Уникальный идентификатор задачи")
    status: AnalysisStatus = Field(..., description="Текущий статус задачи")
    progress: int = Field(
        default=0, ge=0, le=100, description="Прогресс выполнения (0-100%)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": 50,
            }
        }
