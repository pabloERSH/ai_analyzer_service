from fastapi import APIRouter, HTTPException, Depends, Form
from app.api.schemas.analysis import AnalysisResponse, TaskStatus, AnalysisStatus
from app.api.dependencies import get_current_user, get_token_from_header
from app.api.services.auth import AuthenticatedUser
from app.api.services.analyzer import AnalysisService
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Временное хранилище задач (позже заменим на БД)
tasks_store = {}


@router.post("/analysis", response_model=AnalysisResponse)
async def create_analysis(
    period_days: int = Form(default=7, ge=3, le=31),
    analysis_type: str = Form(default="full", pattern="^(full|nutrition|training)$"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header),
):
    """
    Создаёт задачу на AI-анализ.

    Принимает form-data:
    - period_days: глубина анализа в днях (3-31)
    - analysis_type: full, nutrition или training

    Возвращает task_id для отслеживания статуса.
    """
    task_id = str(uuid.uuid4())

    task = {
        "task_id": task_id,
        "status": AnalysisStatus.PENDING,
        "telegram_id": current_user.telegram_id,
        "period_days": period_days,
        "analysis_type": analysis_type,
        "result": None,
        "created_at": datetime.now(),
        "completed_at": None,
        "error_message": None,
    }

    tasks_store[task_id] = task

    try:
        analysis_service = AnalysisService()
        result = await analysis_service.analyze_user_data(
            token=token, period_days=period_days
        )

        task["status"] = AnalysisStatus.COMPLETED
        task["completed_at"] = datetime.now()
        task["result"] = result

        logger.info(f"Task {task_id} completed successfully")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        task["status"] = AnalysisStatus.FAILED
        task["completed_at"] = datetime.now()
        task["error_message"] = str(e)

    return AnalysisResponse(**task)


@router.get("/analysis/{task_id}/status", response_model=TaskStatus)
async def get_task_status(
    task_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Проверка статуса задачи (для polling)"""
    task = tasks_store.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if task["telegram_id"] != current_user.telegram_id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    progress = (
        100
        if task["status"] in (AnalysisStatus.COMPLETED, AnalysisStatus.FAILED)
        else 50
    )

    return TaskStatus(task_id=task_id, status=task["status"], progress=progress)


@router.get("/analysis/{task_id}/result", response_model=AnalysisResponse)
async def get_analysis_result(
    task_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Получение результата анализа"""
    task = tasks_store.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    if task["telegram_id"] != current_user.telegram_id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    if task["status"] == AnalysisStatus.PENDING:
        raise HTTPException(status_code=400, detail="Анализ ещё не начат")

    if task["status"] == AnalysisStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Анализ ещё не завершён")

    if task["status"] == AnalysisStatus.FAILED:
        raise HTTPException(
            status_code=500, detail=task.get("error_message", "Ошибка анализа")
        )

    return AnalysisResponse(**task)
