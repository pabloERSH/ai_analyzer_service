from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health

app = FastAPI(
    title="AI Analyzer Service",
    description="Сервис интеллектуального анализа питания и тренировок",
    version="0.1.0",
)

# CORS для Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В production ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(health.router, prefix="/api/v1", tags=["health"])
#app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
