#!/bin/bash
set -e

# Выполнение миграций Alembic
echo "Running database migrations..."
cd /app/backend

# Убеждаемся, что переменная DATABASE_URL установлена
if [ -z "$DATABASE_URL" ]; then
    echo "WARNING: DATABASE_URL not set, using default"
    export DATABASE_URL="sqlite+aiosqlite:////app/data/b24_analytics.db"
fi

echo "Using DATABASE_URL: $DATABASE_URL"

# Проверяем текущую версию миграций
CURRENT_VERSION_OUTPUT=$(uv run alembic current 2>&1 || echo "")
if echo "$CURRENT_VERSION_OUTPUT" | grep -q "version_num"; then
    CURRENT_VERSION=$(echo "$CURRENT_VERSION_OUTPUT" | grep "version_num" | awk '{print $NF}')
    echo "Current migration version: $CURRENT_VERSION"
else
    echo "No migration version recorded"
    
    # Проверяем, существует ли база и есть ли таблицы
    DB_PATH=$(echo "$DATABASE_URL" | sed 's|sqlite+aiosqlite:///||')
    if [ -f "$DB_PATH" ]; then
        echo "Database file exists, checking if tables exist..."
        
        # Проверяем наличие таблиц через синхронный sqlite3
        # Передаем DATABASE_URL через переменную окружения
        TABLES_EXIST=$(DATABASE_URL="$DATABASE_URL" uv run python3 << 'PYTHON_SCRIPT'
import sqlite3
import os

db_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:////app/data/b24_analytics.db')
db_path = db_url.replace('sqlite+aiosqlite:///', '')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('users', 'mcp_servers', 'mcp_tools')")
    tables = cursor.fetchall()
    conn.close()
    if len(tables) >= 3:
        print('YES')
    else:
        print('NO')
except Exception:
    print('NO')
PYTHON_SCRIPT
)
        
        if [ "$TABLES_EXIST" = "YES" ]; then
            echo "Tables exist but migrations not recorded. Stamping database with head version..."
            uv run alembic stamp head
            echo "✓ Database stamped with head version"
        else
            echo "Tables don't exist, will create them through migrations"
        fi
    else
        echo "Database file does not exist, will be created by migrations"
    fi
fi

# Применяем все миграции до head
echo "Applying all migrations to head..."
if uv run alembic upgrade head; then
    echo "✓ Migrations applied successfully"
    echo "Final migration version:"
    uv run alembic current 2>&1 || echo "  (No version recorded)"
else
    echo "✗ ERROR: Failed to apply migrations"
    exit 1
fi

# Запуск приложения
echo "Starting application..."
cd /app/backend
exec "$@"
