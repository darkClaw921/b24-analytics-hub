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
            echo "Tables exist but migrations not recorded."
            echo "Checking if we need to apply migrations or just stamp..."
            
            # Проверяем наличие критических колонок перед штампованием
            MISSING_COLS=$(DATABASE_URL="$DATABASE_URL" uv run python3 << 'PYTHON_SCRIPT'
import sqlite3
import os

db_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:////app/data/b24_analytics.db')
db_path = db_url.replace('sqlite+aiosqlite:///', '')

missing = []
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем наличие колонок в mcp_tools
    cursor.execute("PRAGMA table_info(mcp_tools)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'hidden_parameters' not in columns:
        missing.append('hidden_parameters')
    if 'parameter_display_names' not in columns:
        missing.append('parameter_display_names')
    
    conn.close()
    
    if missing:
        print(','.join(missing))
    else:
        print('OK')
except Exception as e:
    print(f'ERROR:{str(e)}')
PYTHON_SCRIPT
)
            
            if [ "$MISSING_COLS" = "OK" ]; then
                echo "All columns exist, stamping database with head version..."
                uv run alembic stamp head
                echo "✓ Database stamped with head version"
            else
                echo "Missing columns detected: $MISSING_COLS"
                echo "Will apply migrations instead of stamping..."
                # Не штампуем, позволим миграциям примениться ниже
            fi
        else
            echo "Tables don't exist, will create them through migrations"
        fi
    else
        echo "Database file does not exist, will be created by migrations"
    fi
fi

# Применяем все миграции до head
echo "Applying all migrations to head..."
echo "Available migrations:"
uv run alembic history 2>&1 | head -20 || echo "  (Could not list migrations)"

if uv run alembic upgrade head; then
    echo "✓ Migrations applied successfully"
    echo "Final migration version:"
    uv run alembic current 2>&1 || echo "  (No version recorded)"
else
    echo "✗ WARNING: Failed to apply migrations via Alembic, will check and fix manually"
    # Не выходим с ошибкой, продолжаем проверку колонок
fi

# Проверяем наличие критических колонок и применяем миграции вручную, если нужно
echo "Verifying critical columns exist..."
DB_PATH=$(echo "$DATABASE_URL" | sed 's|sqlite+aiosqlite:///||')
if [ -f "$DB_PATH" ]; then
    MISSING_COLUMNS=$(DATABASE_URL="$DATABASE_URL" uv run python3 << 'PYTHON_SCRIPT'
import sqlite3
import os

db_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:////app/data/b24_analytics.db')
db_path = db_url.replace('sqlite+aiosqlite:///', '')

missing = []
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем наличие колонок в mcp_tools
    cursor.execute("PRAGMA table_info(mcp_tools)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'hidden_parameters' not in columns:
        missing.append('hidden_parameters')
    
    conn.close()
    
    if missing:
        print(','.join(missing))
    else:
        print('OK')
except Exception as e:
    print(f'ERROR:{str(e)}')
PYTHON_SCRIPT
)
    
    if [ "$MISSING_COLUMNS" != "OK" ] && [ -n "$MISSING_COLUMNS" ]; then
        if echo "$MISSING_COLUMNS" | grep -q "ERROR"; then
            echo "Warning: Could not verify columns: $MISSING_COLUMNS"
        else
            echo "Warning: Missing columns detected: $MISSING_COLUMNS"
            echo "Attempting to apply missing migrations manually..."
            
            # Применяем конкретную миграцию, если колонка отсутствует
            if echo "$MISSING_COLUMNS" | grep -q "hidden_parameters"; then
                echo "Applying hidden_parameters migration..."
                # Проверяем текущую версию миграции
                CURRENT_VER=$(uv run alembic current 2>&1 | grep "version_num" | awk '{print $NF}' || echo "")
                echo "Current migration version: $CURRENT_VER"
                
                # Если версия уже head, но колонка отсутствует, делаем downgrade
                if [ "$CURRENT_VER" = "add_hidden_parameters" ] || echo "$CURRENT_VER" | grep -q "head"; then
                    echo "Version is already head but column missing, downgrading first..."
                    uv run alembic downgrade add_parameter_display_names 2>&1 || echo "Downgrade may have failed, continuing..."
                fi
                
                # Затем применяем миграцию заново
                MIGRATION_SUCCESS=false
                if uv run alembic upgrade add_hidden_parameters 2>&1; then
                    echo "✓ Migration command completed, verifying column was created..."
                    # Проверяем, действительно ли колонка создана
                    sleep 1  # Даем время на завершение транзакции
                    COLUMN_EXISTS=$(DATABASE_URL="$DATABASE_URL" uv run python3 << 'PYTHON_SCRIPT'
import sqlite3
import os

db_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:////app/data/b24_analytics.db')
db_path = db_url.replace('sqlite+aiosqlite:///', '')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(mcp_tools)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    
    if 'hidden_parameters' in columns:
        print('YES')
    else:
        print('NO')
except Exception as e:
    print(f'ERROR:{str(e)}')
PYTHON_SCRIPT
)
                    
                    if [ "$COLUMN_EXISTS" = "YES" ]; then
                        echo "✓ Column verified successfully"
                        MIGRATION_SUCCESS=true
                    else
                        echo "WARNING: Migration reported success but column still missing"
                        MIGRATION_SUCCESS=false
                    fi
                else
                    echo "Migration command failed"
                    MIGRATION_SUCCESS=false
                fi
                
                # Если миграция не применилась или колонка все еще отсутствует
                if [ "$MIGRATION_SUCCESS" != "true" ]; then
                    echo "Applying SQL directly to create column..."
                    DATABASE_URL="$DATABASE_URL" uv run python3 << 'PYTHON_SCRIPT'
import sqlite3
import os

db_url = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:////app/data/b24_analytics.db')
db_path = db_url.replace('sqlite+aiosqlite:///', '')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Проверяем, существует ли колонка
    cursor.execute("PRAGMA table_info(mcp_tools)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'hidden_parameters' not in columns:
        print("Adding hidden_parameters column directly...")
        cursor.execute("ALTER TABLE mcp_tools ADD COLUMN hidden_parameters TEXT")
        conn.commit()
        print("✓ Column added successfully")
        
        # Обновляем версию миграции в alembic_version
        cursor.execute("SELECT version_num FROM alembic_version")
        current_version = cursor.fetchone()
        if current_version:
            # Проверяем, не является ли текущая версия уже add_hidden_parameters
            if current_version[0] != 'add_hidden_parameters':
                cursor.execute("UPDATE alembic_version SET version_num = 'add_hidden_parameters'")
                conn.commit()
                print("✓ Migration version updated")
        else:
            # Если нет записи, создаем её
            cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('add_hidden_parameters')")
            conn.commit()
            print("✓ Migration version created")
    else:
        print("Column already exists")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
PYTHON_SCRIPT
                    if [ $? -eq 0 ]; then
                        echo "✓ Column created successfully via SQL"
                        # После прямого создания колонки, обновляем версию миграции
                        echo "Updating migration version..."
                        uv run alembic stamp add_hidden_parameters || echo "Warning: Could not stamp migration version"
                    else
                        echo "✗ ERROR: Failed to create column via SQL"
                        exit 1
                    fi
                else
                    echo "✓ Migration applied successfully via Alembic"
                fi
            fi
        fi
    else
        echo "✓ All critical columns verified"
    fi
fi

# Запуск приложения
echo "Starting application..."
cd /app/backend
exec "$@"
