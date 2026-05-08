# Builder stage
FROM python:3.13.5-slim AS builder

# Установка системных зависимостей, нужных для сборки некоторых библиотек
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Установка библиотек
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.13.5-slim

# Устанавливаем только runtime зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN addgroup --system --gid 1000 app && \
    adduser --system --uid 1000 --gid 1000 --home /app app

WORKDIR /app

# Копируем зависимости из builder
COPY --from=builder /install /usr/local

# Копируем код проекта (отфильтруется через .dockerignore)
COPY . .

# Меняем владельца
RUN chown -R app:app /app

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Порт приложения
EXPOSE 8000

# FastAPI проект
WORKDIR /app

# Команда запуска
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]