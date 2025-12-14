#!/bin/bash
set -e

# Выполнение миграций Alembic
echo "Running database migrations..."
alembic upgrade head

# Запуск приложения
echo "Starting application..."
exec "$@"
