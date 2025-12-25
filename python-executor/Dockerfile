FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
ADD https://astral.sh/uv/0.9.17/install.sh /uv-installer.sh
# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh
# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Копирование файлов зависимостей
COPY python-executor/pyproject.toml ./python-executor/
COPY python-executor/ ./python-executor/

# Рабочая директория для python-executor
WORKDIR /app/python-executor

# Установка Python зависимостей
RUN uv sync

# Создание директории для кэша
RUN mkdir -p /app/cache

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1

# Выполнение при запуске
COPY python-executor/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8002

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

