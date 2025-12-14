FROM python:3.12-slim
# COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN ls
RUN pwd
WORKDIR /app

# Ensure the installed binary is on th
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
COPY pyproject.toml ./
COPY . ./backend/

# Установка Python зависимостей
RUN uv sync

# Рабочая директория для backend
WORKDIR /app/backend

# Создание директории для базы данных
RUN mkdir -p /app/data

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=sqlite+aiosqlite:///./data/b24_analytics.db

# Выполнение миграций при запуске
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8001

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
