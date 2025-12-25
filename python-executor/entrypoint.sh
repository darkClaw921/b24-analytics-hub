#!/bin/bash
set -e

# Запуск приложения
echo "Starting Python Executor Service..."
cd /app/python-executor
exec "$@"

