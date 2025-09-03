from celery import Celery
from celery.schedules import crontab
import os
from config import REDIS_BROKER_URL

# Настройки брокера и бэкенда
broker_url = REDIS_BROKER_URL
result_backend = REDIS_BROKER_URL

# Настройки задач
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Europe/Moscow'
enable_utc = True

# Настройки worker pool для Linux
worker_pool = "prefork"  # Linux/Ubuntu - используем multiprocessing

# Продакшен настройки для worker'ов
worker_concurrency = 16  # Больше воркеров для высокой нагрузки
worker_max_tasks_per_child = 1000  # Перезапуск воркеров каждые 1000 задач (предотвращает memory leaks)
worker_max_memory_per_child = 200000  # 200MB лимит памяти на воркер (KB)

# Настройки задач для продакшена
task_time_limit = 1800  # 30 минут максимум на задачу
task_soft_time_limit = 1500  # 25 минут мягкий лимит
task_acks_late = True  # Подтверждать задачу только после выполнения
task_reject_on_worker_lost = True  # Отклонять задачу если воркер упал

# Retry политика
task_default_retry_delay = 60  # 1 минута между попытками
task_max_retries = 3  # Максимум 3 попытки

# Настройки для HTTP-запросов
task_annotations = {
    'celery_app.parsing_tasks.parse_sources_task': {
        'time_limit': 1800,
        'soft_time_limit': 1500,
    },
    'celery_app.parsing_tasks.parse_rss_sources_task': {
        'time_limit': 1200,
        'soft_time_limit': 1000,
    },
    'celery_app.parsing_tasks.parse_telegram_sources_task': {
        'time_limit': 1200,
        'soft_time_limit': 1000,
    }
}

# Настройки логирования
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# Настройки расписания (опционально, для будущих периодических задач)
beat_schedule = {
    # Пример: периодическая проверка статуса сессий
    # 'check-sessions-status': {
    #     'task': 'celery_app.tasks.check_sessions_status',
    #     'schedule': crontab(minute=0, hour='*/6'),  # Каждые 6 часов
    # },
}

# Настройки beat
beat_max_loop_interval = 60  # Максимальный интервал проверки расписания
beat_sync_every = 60  # Синхронизация расписания каждые 60 секунд

# Включаем автодискавери задач
imports = (
    'celery_app.auth_tasks',
    'celery_app.parsing_tasks',
)

# Дополнительные настройки для отладки
task_track_started = True

# Создаем экземпляр Celery
celery_app = Celery(
    'auth_tg_service',
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
    worker_prefetch_multiplier=1,
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
    task_annotations=task_annotations,
) 