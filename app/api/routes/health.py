from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "healthy", "service": "AI Analyzer Service", "version": "0.1.0"}
