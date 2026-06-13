- Ключи GigaChat API ([получить можно тут](https://developers.sber.ru))
- Запущенные Auth Service и Diary Service

### Установка

```bash
git clone https://github.com/yourusername/ai-analyzer-service.git
cd ai-analyzer-service

# Настройка окружения
cp .env.example .env
# Отредактируй .env, добавив свои ключи

# Запуск всех сервисов
docker-compose up -d --build
```

### Проверка

```bash
# Health check
curl http://localhost:8002/api/v1/health

# Создать анализ (нужен JWT токен)
curl -X POST http://localhost:8002/api/v1/analysis \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "period_days=7" \
  -F "analysis_type=full"
```

---

## 📡 API

| Метод | Эндпоинт | Авторизация | Описание |
|--------|----------|-------------|----------|
| `GET` | `/api/v1/health` | Нет | Проверка работоспособности |
| `POST` | `/api/v1/analysis` | JWT | Создать задачу на анализ |
| `GET` | `/api/v1/analysis/{task_id}/status` | JWT | Проверить статус задачи |
| `GET` | `/api/v1/analysis/{task_id}/result` | JWT | Получить результат анализа |

---

## 🛠️ Технологии

| Технология | Назначение |
|------------|------------|
| **FastAPI** | Асинхронный REST API |
| **Celery** | Фоновые задачи |
| **Redis** | Брокер сообщений + кэш |
| **PostgreSQL** | Хранение истории анализов |
| **GigaChat** | ИИ для анализа |
| **httpx** | Асинхронные HTTP-запросы |
| **PyJWT** | Валидация JWT-токенов |
| **Docker** | Контейнеризация |

---

## ⚙️ Настройка

Все параметры в \`.env\`:

```env
# GigaChat API
GIGACHAT_API_KEY=ваш_client_secret
GIGACHAT_CLIENT_ID=ваш_client_id
GIGACHAT_MODEL=GigaChat:latest
GIGACHAT_TEMPERATURE=0.7
GIGACHAT_MAX_TOKENS=2000

# Внешние сервисы
DIARY_SERVICE_URL=http://nutrition-trecker:8000/api/v1

# JWT (должен совпадать с Auth Service)
JWT_SECRET_KEY=общий-секретный-ключ
JWT_ALGORITHM=HS256

# Redis
REDIS_URL=redis://ai-analyzer-redis:6379/0
REDIS_PASSWORD=redispass123

# База данных
DATABASE_URL=postgresql+asyncpg://postgres:postgres@ai-analyzer-db:5432/ai_analyzer
```

---

## 📂 Структура проекта

```
ai_analyzer_service/
├── app/
│   ├── api/
│   │   ├── dependencies.py    # Зависимости FastAPI (авторизация)
│   │   └── routes/            # Эндпоинты API
│   ├── models/                # SQLAlchemy модели
│   ├── schemas/               # Pydantic схемы
│   ├── services/              # Бизнес-логика
│   │   ├── analyzer.py        # Оркестратор анализа
│   │   ├── diary.py           # Клиент Diary Service
│   │   ├── gigachat_auth.py   # OAuth GigaChat
│   │   ├── gigachat_client.py # Клиент GigaChat API
│   │   └── prompt_builder.py  # Системный промпт
│   ├── tasks/                 # Celery задачи
│   ├── config.py              # Настройки
│   └── main.py                # Приложение FastAPI
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
└── .env.example
```

---

## 🧪 Нагрузочное тестирование

```bash
# Установка locust
pip install locust

# Запуск тестов (mock-эндпоинты, токены GigaChat не тратятся)
locust -f locustfile.py --host=http://localhost:8002 --web-port 8090
```