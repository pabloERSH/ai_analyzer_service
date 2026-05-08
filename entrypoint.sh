#!/bin/sh
set -e

echo "Starting AI Analyzer Service..."

# Если нужны миграции (пока закомментируем, т.к. БД ещё не настроили)
# echo "Running database migrations..."
# alembic upgrade head

echo "Starting application..."
exec "$@"