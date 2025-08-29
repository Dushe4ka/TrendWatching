# Vectorization Service

Микросервис для векторизации спарсенных данных из MongoDB в векторное хранилище Qdrant.

## Описание

Этот микросервис отвечает за:
- Получение невекторизованных записей из MongoDB
- Векторизацию текстовых данных с помощью OpenAI
- Сохранение векторов в Qdrant
- Обновление статуса векторизации в MongoDB

## Установка и запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
DB_NAME=trendwatching

# Redis для Celery
REDIS_BROKER_URL=redis://localhost:6379/2
REDIS_RESULT_BACKEND=redis://localhost:6379/2

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Telegram Bot (для уведомлений)
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_CHAT_ID=your_chat_id
```

### 3. Запуск сервиса
```bash
# Запуск FastAPI сервера
python main.py

# Запуск Celery worker (в отдельном терминале)
celery -A vectorization_tasks worker --loglevel=info
```

## API Endpoints

### POST /vectorization/start
Запускает процесс векторизации.

**Параметры:**
- `chat_id` (опционально): ID чата для уведомлений
- `force` (опционально): Принудительный запуск даже если нет данных

**Пример запроса:**
```json
{
  "chat_id": "123456789",
  "force": false
}
```

**Ответ:**
```json
{
  "task_id": "task-uuid",
  "status": "started",
  "message": "Векторизация запущена",
  "vectorized_count": 0,
  "total_unvectorized": 150
}
```

### GET /vectorization/status/{task_id}
Получает статус задачи векторизации.

**Ответ:**
```json
{
  "task_id": "task-uuid",
  "status": "completed",
  "message": "Векторизация завершена успешно!",
  "vectorized_count": 150,
  "total_unvectorized": 150
}
```

### GET /vectorization/stats
Получает общую статистику векторизации.

**Ответ:**
```json
{
  "total_records": 1000,
  "vectorized_records": 850,
  "unvectorized_records": 150,
  "vectorization_percentage": 85.0
}
```

## Интеграция с auth_tg_service

Микросервис автоматически вызывается после завершения парсинга в `auth_tg_service`. Для этого добавьте в `.env` файл `auth_tg_service`:

```env
VECTORIZATION_SERVICE_URL=http://localhost:8001
```

## Структура проекта

```
vectorization_service/
├── main.py                 # FastAPI приложение
├── vectorization_tasks.py  # Celery задачи
├── database.py            # Работа с MongoDB
├── vector_store.py        # Работа с Qdrant (скопирован из бота)
├── requirements.txt       # Зависимости
└── README.md             # Документация
```

## Логирование

Сервис использует стандартное логирование Python. Логи включают:
- Запуск/завершение задач векторизации
- Количество обработанных записей
- Ошибки при работе с API
- Уведомления в Telegram

## Мониторинг

Для мониторинга состояния сервиса используйте:
- `/vectorization/stats` - общая статистика
- `/vectorization/status/{task_id}` - статус конкретной задачи
- Логи Celery worker'а
- Уведомления в Telegram 