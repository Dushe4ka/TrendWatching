import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.triggers.cron import CronTrigger
from pymongo import MongoClient
from celery_app.tasks.digest_tasks import send_telegram_digest
from logger_config import setup_logger
from telegram_channels_service import telegram_channels_service

logger = setup_logger("apscheduler_digest")

MONGO_URL = 'mongodb://localhost:27017/'
MONGO_DB = 'apscheduler'
MONGO_COLLECTION = 'jobs'

mongo_client = MongoClient(MONGO_URL)
jobstores = {
    'default': MongoDBJobStore(client=mongo_client, database=MONGO_DB, collection=MONGO_COLLECTION)
}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone='Europe/Moscow')

# --- API для управления задачами ---
async def add_digest_job(channel_id, digest_id, category, time_str):
    hour, minute = map(int, time_str.split(':'))
    job_id = f"send_digest_{digest_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
    scheduler.add_job(
        send_digest_job,
        trigger=CronTrigger(hour=hour, minute=minute),
        args=[channel_id, digest_id, category, time_str],
        id=job_id,
        replace_existing=True
    )
    logger.info(f"[APScheduler] Дайджест {digest_id} добавлен/обновлен в расписание на {time_str}")

async def remove_digest_job(digest_id):
    job_id = f"send_digest_{digest_id}"
    try:
        scheduler.remove_job(job_id)
        logger.info(f"[APScheduler] Дайджест {digest_id} удалён из расписания")
    except Exception as e:
        logger.warning(f"[APScheduler] Не удалось удалить дайджест {digest_id}: {e}")

async def update_digest_job(channel_id, digest_id, category, new_time):
    await remove_digest_job(digest_id)
    await add_digest_job(channel_id, digest_id, category, new_time)

async def get_digest_jobs():
    return [job for job in scheduler.get_jobs() if job.id.startswith('send_digest_')]

async def init_digest_jobs_from_db(active_digests):
    # active_digests: список словарей с ключами channel_id, digest_id, category, time
    for d in active_digests:
        await add_digest_job(d['channel_id'], d['digest_id'], d['category'], d['time'])
    logger.info(f"[APScheduler] Инициализировано {len(active_digests)} задач из БД")

# --- Функция-джоб для отправки дайджеста ---
def send_digest_job(channel_id, digest_id, category, time_str):
    # time_str не используется, но нужен для совместимости с args
    send_telegram_digest.delay(channel_id, digest_id, category)
    logger.info(f"[APScheduler] Запущена отправка дайджеста {digest_id} для канала {channel_id}")

# --- Запускать при старте бота/админки ---
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("[APScheduler] Scheduler запущен")
        # Автоматическая инициализация задач из БД (асинхронно)
        active_digests = telegram_channels_service.get_active_digests()
        asyncio.create_task(init_digest_jobs_from_db(active_digests))
        logger.info(f"[APScheduler] Автоматически инициализировано {len(active_digests)} задач из БД при старте")