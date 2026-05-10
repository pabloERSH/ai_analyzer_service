from fastapi import APIRouter, HTTPException, Form
from app.api.schemas.analysis import AnalysisResponse, TaskStatus, AnalysisStatus
from datetime import datetime
import uuid
import random
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Отдельное хранилище для тестовых задач
test_tasks_store = {}


@router.post("/analysis/load-test", response_model=AnalysisResponse)
async def create_load_test(
    period_days: int = Form(default=7, ge=3, le=31),
    analysis_type: str = Form(default="full", pattern="^(full|nutrition|training)$"),
):
    """Создать тестовую задачу анализа (без GigaChat)"""
    from app.tasks.analysis_tasks import analyze_user_data_test_task
    
    task_id = str(uuid.uuid4())
    
    task = {
        "task_id": task_id,
        "status": AnalysisStatus.PENDING,
        "telegram_id": 999999999,
        "period_days": period_days,
        "analysis_type": analysis_type,
        "source": None,
        "result": None,
        "created_at": datetime.now(),
        "completed_at": None,
        "error_message": None,
    }
    
    celery_task = analyze_user_data_test_task.delay(
        token="load_test_token",
        period_days=period_days
    )
    task["celery_task_id"] = celery_task.id
    
    test_tasks_store[task_id] = task
    logger.info(f"Load test task {task_id} created")
    return AnalysisResponse(**task)


@router.get("/analysis/load-test/{task_id}/status", response_model=TaskStatus)
async def get_load_test_status(task_id: str):
    """Статус тестовой задачи"""
    task = test_tasks_store.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    _update_task_from_celery(task)
    
    progress = 100 if task["status"] in (AnalysisStatus.COMPLETED, AnalysisStatus.FAILED) else 50
    return TaskStatus(task_id=task_id, status=task["status"], progress=progress)


@router.get("/analysis/load-test/{task_id}/result", response_model=AnalysisResponse)
async def get_load_test_result(task_id: str):
    """Результат тестовой задачи"""
    task = test_tasks_store.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    _update_task_from_celery(task)
    
    if task["status"] != AnalysisStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Анализ ещё не завершён")
    
    return AnalysisResponse(**task)


def _update_task_from_celery(task: dict):
    """Обновляет статус задачи из Celery"""
    from app.tasks.analysis_tasks import analyze_user_data_test_task
    
    celery_task_id = task.get("celery_task_id")
    if not celery_task_id:
        return
    
    celery_result = analyze_user_data_test_task.AsyncResult(celery_task_id)
    
    if celery_result.state == "STARTED":
        task["status"] = AnalysisStatus.PROCESSING
    elif celery_result.ready():
        if celery_result.successful():
            task["status"] = AnalysisStatus.COMPLETED
            task["completed_at"] = datetime.now()
            task["result"] = celery_result.result
        else:
            task["status"] = AnalysisStatus.FAILED
            task["completed_at"] = datetime.now()
            task["error_message"] = str(celery_result.info)
