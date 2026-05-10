from fastapi import APIRouter, HTTPException, Depends, Form
from app.api.schemas.analysis import AnalysisResponse, TaskStatus, AnalysisStatus
from app.api.dependencies import get_current_user, get_token_from_header
from app.api.services.auth import AuthenticatedUser
from app.tasks.analysis_tasks import analyze_user_data_task
from datetime import datetime
from app.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
tasks_store = {}


@router.post("/analysis", response_model=AnalysisResponse)
async def create_analysis(    
    period_days: int = Form(default=7, ge=3, le=31),
    analysis_type: str = Form(default="full", pattern="^(full|nutrition|training)$"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header),
    ):

    task_id = str(uuid.uuid4())
    
    task = {
        "task_id": task_id,
        "status": AnalysisStatus.PENDING,
        "telegram_id": current_user.telegram_id,
        "period_days": period_days,
        "analysis_type": analysis_type,
        "source": None,
        "result": None,
        "created_at": datetime.now(),
        "completed_at": None,
        "error_message": None,
    }
    
    # Проверяем кэш
    try:
        from app.api.services.analysis_cache import get_cached_by_task
        cached_result = await get_cached_by_task(
            telegram_id=current_user.telegram_id,
            period_days=period_days,
        )
        if cached_result:
            task["status"] = AnalysisStatus.COMPLETED
            task["completed_at"] = datetime.now()
            task["source"] = "cache"
            task["result"] = cached_result
            tasks_store[task_id] = task
            return AnalysisResponse(**task)
    except Exception as e:
        logger.warning(f"Cache check failed: {e}")
    
    tasks_store[task_id] = task
    
    # Запускаем Celery
    celery_task = analyze_user_data_task.delay(token=token, period_days=period_days)
    task["celery_task_id"] = celery_task.id
    
    return AnalysisResponse(**task)


@router.get("/analysis/{task_id}/status", response_model=TaskStatus)
async def get_task_status(
    task_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Проверка статуса задачи (polling)"""
    task = tasks_store.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task["telegram_id"] != current_user.telegram_id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    # Проверяем Celery
    celery_task_id = task.get("celery_task_id")
    if celery_task_id:
        celery_result = analyze_user_data_task.AsyncResult(celery_task_id)

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
    """Получение результата"""
    task = tasks_store.get(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task["telegram_id"] != current_user.telegram_id:
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    # Проверяем Celery
    celery_task_id = task.get("celery_task_id")
    if celery_task_id:
        celery_result = analyze_user_data_task.AsyncResult(celery_task_id)

        if celery_result.ready() and celery_result.successful():
            task["status"] = AnalysisStatus.COMPLETED
            task["completed_at"] = datetime.now()
            task["result"] = celery_result.result

            # Сохраняем в БД и кэш
            result = celery_result.result
            report = result.get("report", {})
            analysis = result.get("analysis", {})

            # Кэш в Redis
            try:
                from app.api.services.analysis_cache import set_cached

                await set_cached(
                    telegram_id=task["telegram_id"],
                    period_start=report.get("period", {}).get("start", ""),
                    period_end=report.get("period", {}).get("end", ""),
                    result=result,
                )
            except Exception as e:
                logger.warning(f"Failed to cache: {e}")

            # Сохранение в БД
            try:
                from app.api.services.analysis_storage import save_analysis

                await save_analysis(
                    task_id=task_id,
                    telegram_id=task["telegram_id"],
                    period_days=task["period_days"],
                    period_start=report.get("period", {}).get("start", ""),
                    period_end=report.get("period", {}).get("end", ""),
                    analysis_type=task["analysis_type"],
                    report=report,
                    analysis=analysis,
                    llm_model=settings.GIGACHAT_MODEL,
                )
            except Exception as e:
                logger.warning(f"Failed to save to DB: {e}")

    if task["status"] != AnalysisStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Анализ ещё не завершён")

    return AnalysisResponse(**task)
