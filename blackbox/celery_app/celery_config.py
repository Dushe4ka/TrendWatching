from celery.schedules import crontab

# Настройки брокера и бэкенда - используем разные базы данных Redis для разных сервисов
broker_url = 'redis://:Ollama12357985@127.0.0.1:14571/0'
result_backend = 'redis://:Ollama12357985@127.0.0.1:14571/0'

# Настройки задач
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Europe/Moscow'
enable_utc = True

# Настройки worker pool для Linux
worker_pool = 'prefork'  # Используем prefork пул для Linux

worker_concurrency = 15  # Количество воркеров
worker_prefetch_multiplier = 4  # Каждый воркер берет по 4 задаче
worker_max_tasks_per_child = 500  # Перезапуск воркера после 500 задач
worker_max_memory_per_child = 250000  # Перезапуск воркера при превышении памяти (в КБ)

# Настройки логирования
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Настройки расписания
beat_schedule = {
    'generate-daily-digests': {
        'task': 'celery_app.tasks.news_tasks.generate_daily_digests',
        'schedule': crontab(hour=13, minute=0),  # Каждый день в 13:00
    },
    'send-daily-news': {
        'task': 'celery_app.tasks.news_tasks.send_daily_news',
        'schedule': crontab(hour=14, minute=0),  # Каждый день в 14:00
    },
    # 'periodic-telegram-auth-check': {
    #     'task': 'celery_app.tasks.auth_TG.periodic_telegram_auth_check',
    #     'schedule': crontab(minute=0, hour='*/6'),  # Каждый 6 часов
    # },
    # Парсинг всех источников каждые 6 часов
    'parse-all-sources-every-6-hours': {
        'task': 'celery_app.tasks.parsing_tasks.periodic_parse_all_sources',
        'schedule': crontab(minute=0, hour='*/6'),  # Каждые 6 часов
    },
}

# Настройки beat
beat_max_loop_interval = 60  # Максимальный интервал проверки расписания
beat_sync_every = 60  # Синхронизация расписания каждые 60 секунд

# Включаем автодискавери задач
imports = (
    'celery_app.tasks.csv_processing_tasks',
    'celery_app.tasks.trend_analysis_tasks',
    'celery_app.tasks.news_tasks',
    'celery_app.tasks.vectorization_tasks',
    'celery_app.tasks.auth_TG',
    'celery_app.tasks.weekly_news_tasks',
    'celery_app.tasks.parsing_tasks',
    'celery_app.tasks.digest_tasks',
)

# Дополнительные настройки для отладки
task_track_started = True
task_time_limit = 7200  # Максимальное время выполнения задачи (2 часа)
task_soft_time_limit = 6000  # Мягкое ограничение времени (100 минут)
task_acks_late = True  # Подтверждение задачи только после выполнения
task_reject_on_worker_lost = True  # Отклонение задачи при потере воркера
task_default_retry_delay = 300  # Задержка перед повторной попыткой (5 минут)
task_max_retries = 3  # Максимальное количество повторных попыток

celery_app = Celery(
    'blackbox',
    broker=broker_url,
    backend=result_backend
)

# Применяем конфигурацию
celery_app.conf.update(
    task_serializer=task_serializer,
    result_serializer=result_serializer,
    accept_content=accept_content,
    timezone=timezone,
    enable_utc=enable_utc,
    worker_pool=worker_pool,
    worker_concurrency=worker_concurrency,
    worker_prefetch_multiplier=worker_prefetch_multiplier,
    worker_max_tasks_per_child=worker_max_tasks_per_child,
    worker_max_memory_per_child=worker_max_memory_per_child,
    worker_log_format=worker_log_format,
    worker_task_log_format=worker_task_log_format,
    beat_schedule=beat_schedule,
    beat_max_loop_interval=beat_max_loop_interval,
    beat_sync_every=beat_sync_every,
    imports=imports,
    task_track_started=task_track_started,
    task_time_limit=task_time_limit,
    task_soft_time_limit=task_soft_time_limit,
    task_acks_late=task_acks_late,
    task_reject_on_worker_lost=task_reject_on_worker_lost,
    task_default_retry_delay=task_default_retry_delay,
    task_max_retries=task_max_retries,
)