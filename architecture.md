# Архитектура B24 Analytics Hub

## Общее описание

B24 Analytics Hub - веб-приложение для аналитики данных из Bitrix24 с интеллектуальным чатом, использующим LLM и MCP инструменты, и системой дашбордов с динамическими чартами.

## Технологический стек

### Backend
- **FastAPI** - веб-фреймворк
- **SQLAlchemy 2.0 (async)** - ORM для работы с БД
- **SQLite + aiosqlite** - база данных
- **OpenAI API** - интеграция с GPT-4
- **langchain-mcp-adapters** - подключение к MCP серверам
- **tiktoken** - подсчет токенов
- **python-jose** - JWT токены
- **passlib** - хеширование паролей
- **httpx** - HTTP клиент для связи с Python Executor Service

### Frontend
- **React 18 + TypeScript** - UI фреймворк
- **Vite** - сборщик и preview сервер для production
- **React Router** - маршрутизация
- **Axios** - HTTP клиент
- **Recharts** - библиотека для визуализации чартов

### Docker
- **Docker Compose** - оркестрация сервисов
- **Backend Dockerfile** - контейнеризация FastAPI приложения (Python 3.12)
- **Frontend Dockerfile** - сборка React приложения с запуском через Vite preview
- **Volumes** - хранение данных базы данных SQLite

### База данных (SQLite)
- **users** - пользователи системы
- **chats** - чаты пользователей
- **messages** - сообщения в чатах
- **chat_contexts** - контекст чатов (токены)
- **mcp_servers** - конфигурация MCP серверов
- **mcp_tools** - инструменты MCP
- **dashboards** - дашборды пользователей
- **charts** - чарты в дашбордах

## Структура проекта


```
b24-analytics-hub/
├── backend/                    # FastAPI приложение
│   ├── app/
│   │   ├── api/                # API endpoints
│   │   │   ├── admin.py        # Админ-панель endpoints
│   │   │   ├── auth.py         # Авторизация endpoints
│   │   │   ├── chats.py        # Чаты endpoints
│   │   │   ├── mcp.py          # MCP инструменты endpoints
│   │   │   ├── messages.py     # Сообщения endpoints
│   │   │   ├── users.py        # Пользователи endpoints
│   │   │   └── dashboards.py   # Дашборды и чарты endpoints
│   │   ├── models/             # SQLAlchemy модели
│   │   │   ├── chat.py         # Модели Chat, Message, ChatContext
│   │   │   ├── mcp_config.py   # Модели MCPServer, MCPTool
│   │   │   ├── user.py         # Модель User
│   │   │   └── dashboard.py    # Модели Dashboard, Chart
│   │   ├── services/           # Бизнес-логика
│   │   │   ├── chat_service.py # Логика чата с OpenAI и MCP
│   │   │   ├── mcp_service.py  # Подключение к MCP серверам
│   │   │   ├── token_service.py # Подсчет токенов
│   │   │   ├── user_service.py # CRUD пользователей
│   │   │   └── dashboard_service.py # CRUD дашбордов и чартов, выполнение Python кода
│   │   ├── auth.py             # JWT токены, хеширование паролей
│   │   ├── config.py           # Конфигурация приложения
│   │   ├── database.py         # Настройка SQLAlchemy
│   │   ├── dependencies.py     # FastAPI зависимости
│   │   └── main.py             # FastAPI приложение, роутинг, WebSocket
│   ├── alembic/                # Миграции БД
│   │   ├── versions/           # Файлы миграций
│   │   ├── env.py              # Конфигурация Alembic
│   │   └── script.py.mako      # Шаблон миграций
│   ├── tests/                  # Тесты
│   ├── create_admin.py         # Скрипт создания администратора
│   ├── Dockerfile              # Docker образ для backend
│   ├── entrypoint.sh           # Скрипт запуска с миграциями
│   ├── alembic.ini             # Конфигурация Alembic
│   ├── pyproject.toml          # Python зависимости
│   └── uv.lock                 # Lock файл зависимостей
├── python-executor/            # Python Executor Service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI приложение для выполнения кода
│   │   └── executor.py        # Логика безопасного выполнения Python кода
│   ├── Dockerfile             # Docker образ для executor
│   ├── entrypoint.sh          # Скрипт запуска
│   ├── pyproject.toml         # Python зависимости (restrictedpython)
│   └── uv.lock                # Lock файл зависимостей
├── frontend/                   # React приложение
│   ├── src/
│   │   ├── components/
│   │   │   ├── Admin/          # Компоненты админ-панели
│   │   │   │   ├── AdminPanel.tsx # Главная панель администратора
│   │   │   │   ├── MCPServers.tsx # Управление MCP серверами
│   │   │   │   ├── ToolSettings.tsx # Управление инструментами
│   │   │   │   └── UserManagement.tsx # Управление пользователями
│   │   │   ├── Auth/           # Компоненты авторизации
│   │   │   │   ├── Login.tsx # Форма входа
│   │   │   │   └── ProtectedRoute.tsx # Защита роутов
│   │   │   ├── Chat/           # Компоненты чата
│   │   │   │   ├── ChatWindow.tsx # Окно чата
│   │   │   │   ├── MessageInput.tsx # Поле ввода сообщений
│   │   │   │   ├── MessageList.tsx # Список сообщений с автоскроллом
│   │   │   │   ├── TokenCounter.tsx # Счетчик использованных токенов
│   │   │   │   └── ToolButtons.tsx # Кнопки для прямого вызова MCP инструментов
│   │   │   ├── ChatList/       # Компонент списка чатов
│   │   │   │   └── ChatList.tsx # Список чатов пользователя, создание новых чатов, удаление чатов с подтверждением
│   │   │   ├── Dashboard/      # Компоненты дашбордов
│   │   │   │   ├── DashboardList.tsx # Список дашбордов пользователя
│   │   │   │   ├── DashboardView.tsx # Просмотр дашборда с чартами
│   │   │   │   ├── ChartComponent.tsx # Компонент отрисовки чарта
│   │   │   │   └── ChartEditor.tsx # Редактор чарта с превью
│   │   │   └── Charts/         # Компоненты чартов
│   │   │       ├── LineChart.tsx # Линейный чарт
│   │   │       ├── BarChart.tsx # Столбчатый чарт
│   │   │       ├── PieChart.tsx # Круговой чарт
│   │   │       └── ChartWrapper.tsx # Обертка для выбора типа чарта
│   │   ├── hooks/              # React хуки
│   │   │   ├── useAuth.tsx     # Хук авторизации
│   │   │   └── useChat.ts      # Хук работы с чатом
│   │   ├── services/           # Сервисы для API
│   │   │   ├── api.ts          # Axios клиент
│   │   │   ├── auth.ts         # Сервис авторизации
│   │   │   ├── websocket.ts    # WebSocket подключение
│   │   │   └── dashboards.ts  # Сервис для работы с дашбордами
│   │   ├── styles/             # Стили
│   │   │   └── bitrix24.css    # Основные стили приложения
│   │   ├── types/              # TypeScript типы
│   │   │   └── index.ts        # Определения типов
│   │   ├── App.tsx             # Главный компонент приложения
│   │   └── main.tsx            # Точка входа React
│   ├── Dockerfile              # Docker образ для frontend
│   ├── index.html              # HTML шаблон
│   ├── package.json            # Node.js зависимости
│   ├── package-lock.json       # Lock файл зависимостей
│   ├── tsconfig.json           # TypeScript конфигурация
│   ├── tsconfig.node.json      # TypeScript конфигурация для Node
│   └── vite.config.ts          # Vite конфигурация
├── docker-compose.yml          # Docker Compose конфигурация
├── architecture.md             # Документация архитектуры
└── README.md                   # Описание проекта
```
### Backend (`/backend/app/`)

#### Модели (`models/`)
- **user.py** - модель User для авторизации
- **chat.py** - модели Chat, Message, ChatContext для чатов
- **mcp_config.py** - модели MCPServer, MCPTool для MCP конфигурации (MCPTool содержит поля custom_name, custom_description для кастомного отображения в быстрых инструментах, parameter_display_names для кастомных названий параметров, hidden_parameters для скрытия параметров от пользователя визуально)
- **dashboard.py** - модели Dashboard, Chart для дашбордов (Dashboard содержит user_id, title, description; Chart содержит dashboard_id, title, chart_type, python_code, position_x, position_y, width, height, config)

#### Сервисы (`services/`)
- **user_service.py** - CRUD операции с пользователями, аутентификация
- **mcp_service.py** - подключение к MCP серверам через MultiServerMCPClient, кэширование инструментов, прямой вызов инструментов, синхронизация инструментов из MCP серверов в БД
- **chat_service.py** - логика чата с OpenAI, вызов MCP tools через LLM, управление контекстом
- **token_service.py** - подсчет токенов через tiktoken
- **dashboard_service.py** - CRUD операции с дашбордами и чартами, вызов Python Executor Service для выполнения кода чартов

#### API роуты (`api/`)
- **auth.py** - авторизация (login, refresh token)
- **users.py** - получение текущего пользователя
- **chats.py** - CRUD операции с чатами (создание, получение списка, получение по ID, удаление)
- **messages.py** - отправка сообщений в чат
- **mcp.py** - получение списка инструментов, прямой вызов инструментов
- **admin.py** - админ-панель (управление пользователями, MCP серверами, инструментами, синхронизация инструментов из MCP серверов)
- **dashboards.py** - CRUD операции с дашбордами и чартами, выполнение кода чартов

#### Основные файлы
- **main.py** - FastAPI приложение, роутинг, WebSocket для чата
- **config.py** - конфигурация приложения (переменные окружения, включая OPENAI_MODEL для выбора модели ChatGPT, PYTHON_EXECUTOR_URL и PYTHON_EXECUTOR_TIMEOUT для Python Executor Service)
- **database.py** - настройка async SQLAlchemy, создание сессий
- **auth.py** - JWT токены (создание, проверка), хеширование паролей
- **dependencies.py** - FastAPI зависимости (get_current_user, get_current_admin_user)
- **Dockerfile** - конфигурация Docker образа для backend
- **entrypoint.sh** - скрипт запуска с выполнением миграций Alembic

### Frontend (`/frontend/src/`)

#### Компоненты (`components/`)

**Auth/**
- **Login.tsx** - форма входа
- **ProtectedRoute.tsx** - защита роутов (проверка авторизации и прав)

**ChatList/**
- **ChatList.tsx** - список чатов пользователя, создание новых чатов, удаление чатов с подтверждением

**Chat/**
- **ChatWindow.tsx** - окно чата с WebSocket подключением
- **MessageList.tsx** - список сообщений с автоскроллом
- **MessageInput.tsx** - поле ввода сообщений
- **TokenCounter.tsx** - счетчик использованных токенов
- **ToolButtons.tsx** - кнопки для прямого вызова MCP инструментов

**Admin/**
- **AdminPanel.tsx** - главная панель администратора
- **UserManagement.tsx** - управление пользователями (CRUD)
- **MCPServers.tsx** - управление MCP серверами (CRUD, активация/деактивация)
- **ToolSettings.tsx** - управление инструментами (активация, отметка популярных, редактирование кастомного имени и описания для визуального отображения, редактирование названий параметров, скрытие параметров от пользователя визуально)

**Dashboard/**
- **DashboardList.tsx** - список дашбордов пользователя, создание новых дашбордов, удаление дашбордов
- **DashboardView.tsx** - просмотр дашборда с чартами в grid layout, добавление и удаление чартов
- **ChartComponent.tsx** - компонент отрисовки чарта с кнопкой обновления данных
- **ChartEditor.tsx** - модальное окно для создания/редактирования чарта с полями: title, chart_type, python_code, position, size, превью данных

**Charts/**
- **LineChart.tsx** - линейный чарт на основе Recharts
- **BarChart.tsx** - столбчатый чарт на основе Recharts
- **PieChart.tsx** - круговой чарт на основе Recharts
- **ChartWrapper.tsx** - обертка для выбора типа чарта

#### Сервисы (`services/`)
- **api.ts** - Axios клиент с interceptors для автоматического добавления токенов и refresh
- **auth.ts** - авторизация (login, refresh token, хранение в localStorage)
- **websocket.ts** - WebSocket подключение к чату
- **dashboards.ts** - функции для работы с API дашбордов (getDashboards, createDashboard, getDashboard, updateDashboard, deleteDashboard, createChart, updateChart, deleteChart, executeChart)

#### Хуки (`hooks/`)
- **useAuth.tsx** - AuthContext и хук для работы с авторизацией
- **useChat.ts** - хук для работы с чатом (загрузка сообщений, отправка)

#### Стили (`styles/`)
- **bitrix24.css** - стили в духе Open WebUI (темная тема, современный дизайн, градиенты, адаптивность)

#### Типы (`types/`)
- **index.ts** - TypeScript типы (User, Chat, Message, MCPServer, MCPTool, Dashboard, Chart, ChartType, ChartData и т.д.)

#### Docker файлы
- **Dockerfile** - сборка React приложения и запуск через Vite preview сервер

## Функциональность

### Авторизация
- JWT access токены (срок действия: 30 минут)
- JWT refresh токены (срок действия: 7 дней)
- Автоматическое обновление access токена при истечении
- Хранение токенов в localStorage
- Защита роутов (требуется авторизация / требуются права админа)

### Чат с LLM + MCP
1. Пользователь отправляет сообщение
2. Backend формирует запрос к OpenAI с доступными MCP инструментами
3. LLM автоматически вызывает нужные MCP инструменты (если нужно)
4. Результаты инструментов возвращаются LLM
5. LLM формирует финальный ответ
6. Все сообщения сохраняются в БД с подсчетом токенов

### Прямой вызов MCP инструментов
1. В чате отображаются кнопки популярных инструментов
2. Клик по кнопке открывает модальное окно с параметрами
3. Запрос отправляется напрямую к MCP серверу (минуя LLM)
4. Результат добавляется в чат

### Админ-панель
- **Пользователи**: создание, просмотр, удаление
- **MCP серверы**: добавление, редактирование, активация/деактивация, синхронизация инструментов (автоматически при создании/обновлении активного сервера, или вручную через endpoint)
- **Инструменты**: просмотр всех инструментов, активация/деактивация (какие tools LLM может вызывать), отметка популярных (отображаются как кнопки в чате), редактирование кастомного имени и описания (используются только для визуального отображения в быстрых инструментах), редактирование названий параметров (кастомные названия для визуального отображения), скрытие параметров от пользователя (параметры скрываются визуально в форме вызова инструмента, но отправляются на backend со значениями по умолчанию)

### WebSocket
- Real-time обновления в чате
- Подключение к `/ws/chats/{chat_id}`
- Автоматическое переподключение при разрыве связи

### Дашборды и чарты
1. Пользователь создает дашборд с названием и описанием
2. В дашборде можно создавать чарты разных типов (line, bar, pie)
3. Для каждого чарта указывается Python код, который генерирует данные
4. При просмотре дашборда код выполняется через Python Executor Service
5. Данные возвращаются в формате JSON с labels и datasets
6. Чарты отрисовываются с помощью библиотеки Recharts
7. Пользователь может редактировать код чарта с превью результата
8. Чарты располагаются в grid layout с настраиваемыми позицией и размером

## Интеграция с MCP

### Подключение к Bitrix24 MCP серверу
- URL: `http://0.0.0.0:8000/mcp`
- Транспорт: `streamable_http`
- Имя сервера: `bitrix24-main`

### Использование MultiServerMCPClient
- Инициализация при запуске приложения
- Кэширование метаданных инструментов
- Поддержка нескольких MCP серверов
- Автоматическая передача инструментов в OpenAI

## Python Executor Service

### Описание
Отдельный микросервис для безопасного выполнения Python кода, генерирующего данные для чартов.

### Функциональность
- HTTP endpoint `POST /execute` принимает Python код
- Выполняет код в изолированном контексте с использованием `restrictedpython`
- Ограничения безопасности:
  - Таймаут выполнения (по умолчанию 30 секунд)
  - Запрет опасных операций (file system, network, subprocess)
  - Ограниченный набор встроенных функций
- Ожидает возврат JSON через `print()` или переменную `result`
- Формат данных: `{"labels": [...], "datasets": [{"label": "...", "data": [...], "backgroundColor": "..."}]}`

### Технологии
- **FastAPI** - веб-фреймворк
- **restrictedpython** - безопасное выполнение Python кода
- **Python 3.12** - версия Python

### Интеграция
- Backend вызывает executor через HTTP клиент (httpx)
- URL настраивается через переменную окружения `PYTHON_EXECUTOR_URL`
- Таймаут настраивается через `PYTHON_EXECUTOR_TIMEOUT`

## Безопасность
- JWT токены с коротким сроком действия
- Bcrypt для хеширования паролей
- Защита API endpoints через middleware
- CORS настроен для разработки (в продакшене нужно указать конкретные origins)

## Docker

### Структура Docker файлов
- **docker-compose.yml** - оркестрация backend, frontend и python-executor сервисов
- **backend/Dockerfile** - образ для FastAPI приложения
- **backend/entrypoint.sh** - скрипт запуска с миграциями
- **python-executor/Dockerfile** - образ для Python Executor Service
- **python-executor/entrypoint.sh** - скрипт запуска executor
- **frontend/Dockerfile** - сборка React приложения и запуск через Vite preview
- **.dockerignore** - файлы, исключаемые из Docker контекста

### Запуск через Docker
1. Python Executor сервис:
   - Использует Python 3.12-slim образ
   - Запускает FastAPI приложение для выполнения Python кода
   - Порт 8002 для API
   - Volume `python_executor_cache` для кэша (опционально)

2. Backend сервис:
   - Использует Python 3.12-slim образ
   - Автоматически выполняет миграции Alembic при запуске
   - База данных SQLite хранится в volume `backend_data`
   - Порт 8001 для API и WebSocket
   - Зависит от python-executor сервиса

3. Frontend сервис:
   - Использует Node 20 Alpine образ
   - Собирает React приложение через Vite
   - Запускает Vite preview сервер для раздачи статики
   - Порт 3000 для доступа к приложению
   - Проксирование API и WebSocket запросов настраивается на уровне сервера
   - Зависит от backend сервиса

4. Volumes:
   - `backend_data` - хранение SQLite базы данных
   - `python_executor_cache` - кэш для Python Executor Service

## Дизайн
- Темная тема в стиле Open WebUI
- Цветовая схема: темные фоны (#0f0f23, #1a1a2e, #1e1e3f), градиентные акценты (индиго-фиолетовый)
- Современный минималистичный дизайн с плавными переходами
- Адаптивный дизайн для мобильных устройств
- Градиенты для кнопок и акцентов
- Скругленные углы и тени для глубины
- Анимации и переходы для улучшения UX

