#!/bin/bash
set -e

# Выполнение миграций Alembic
echo "Running database migrations..."
cd /app/backend
uv run alembic upgrade head

# Запуск приложения
echo "Starting application..."
cd /app/backend
exec "$@"
