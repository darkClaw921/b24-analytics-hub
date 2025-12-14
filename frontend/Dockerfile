FROM node:20-alpine

WORKDIR /app

# Копирование package файлов
COPY frontend/package*.json ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода
COPY frontend/ ./

# Сборка приложения (пропускаем проверку типов для быстрой сборки)
RUN npx vite build

EXPOSE 3000

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
