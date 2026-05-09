import logging
from sqlalchemy import select
from app.models.database import async_session
from app.models.analysis import AnalysisResult

logger = logging.getLogger(__name__)


async def save_analysis(
    task_id: str,
    telegram_id: int,
    period_days: int,
    period_start: str,
    period_end: str,
    analysis_type: str,
    report: dict,
    analysis: dict,
    llm_model: str = None,
) -> AnalysisResult:
    """Сохраняет результат анализа в БД."""

    result = AnalysisResult(
        task_id=task_id,
        telegram_id=telegram_id,
        period_days=period_days,
        period_start=period_start,
        period_end=period_end,
        analysis_type=analysis_type,
        status="completed",
        report=report,
        analysis=analysis,
        summary=analysis.get("title", ""),
        rating=analysis.get("overall_verdict", {}).get("rating"),
        llm_model=llm_model,
    )

    async with async_session() as session:
        session.add(result)
        await session.commit()
        logger.info(f"Analysis saved to DB: {task_id}")


async def get_analysis_history(
    telegram_id: int, limit: int = 10
) -> list[AnalysisResult]:
    """Возвращает историю анализов пользователя."""
    async with async_session() as session:
        query = (
            select(AnalysisResult)
            .where(AnalysisResult.telegram_id == telegram_id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        return result.scalars().all()
