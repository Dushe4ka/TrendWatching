import os
import logging
from celery import Celery
from vector_store import VectorStore
from database import get_unvectorized_data_async, update_vectorization_status_async
from telegram_notifications import send_admin_notification

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://:Ollama12357985@127.0.0.1:14571/2")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://:Ollama12357985@127.0.0.1:14571/2")

celery_app = Celery(
    "vectorization_service",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

def run_async(coro):
    """Запускает асинхронную функцию в синхронном контексте"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если loop уже запущен, создаем новый в отдельном потоке
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # Если нет активного loop, создаем новый
        return asyncio.run(coro)

@celery_app.task(bind=True, name="vectorization_service.start_vectorization_task")
def start_vectorization_task(self, chat_id=None, force=False):
    """Задача векторизации невекторизованных данных"""
    try:
        logger.info("🚀 Начинаем процесс векторизации")
        
        # Получаем невекторизованные данные асинхронно
        unvectorized_data = run_async(get_unvectorized_data_async())
        
        if not unvectorized_data and not force:
            message = "⚠️ Нет невекторизованных данных для обработки"
            logger.warning(message)
            send_admin_notification(message, chat_id)
            return {
                "status": "no_data",
                "message": message,
                "vectorized_count": 0,
                "total_unvectorized": 0
            }
        
        logger.info(f"📊 Найдено {len(unvectorized_data)} записей для векторизации")
        
        # Инициализируем векторное хранилище
        vector_store = VectorStore()
        
        # Проверяем размер данных и разбиваем на чанки если нужно
        total_records = len(unvectorized_data)
        max_records_per_batch = 50  # Максимальное количество записей за один запрос к OpenAI
        
        if total_records > max_records_per_batch:
            logger.info(f"📦 Разбиваем {total_records} записей на чанки по {max_records_per_batch}")
            chunks = [unvectorized_data[i:i + max_records_per_batch] 
                     for i in range(0, total_records, max_records_per_batch)]
        else:
            chunks = [unvectorized_data]
        
        total_vectorized = 0
        success = True
        
        # Обрабатываем каждый чанк
        for i, chunk in enumerate(chunks):
            logger.info(f"🔄 Обрабатываем чанк {i+1}/{len(chunks)} ({len(chunk)} записей)")
            
            try:
                # Векторизуем чанк
                chunk_success = vector_store.add_materials(chunk)
                
                if chunk_success:
                    # Обновляем статус векторизации в БД для этого чанка
                    from bson import ObjectId
                    ids_to_update = [ObjectId(x["_id"]) for x in chunk]
                    run_async(update_vectorization_status_async(ids_to_update))
                    
                    total_vectorized += len(chunk)
                    logger.info(f"✅ Чанк {i+1} успешно векторизован ({len(chunk)} записей)")
                else:
                    logger.error(f"❌ Ошибка при векторизации чанка {i+1}")
                    success = False
                    break
                    
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке чанка {i+1}: {e}")
                success = False
                break
        
        if success and total_vectorized > 0:
            message = f"✅ Векторизация завершена успешно!\n\n• Векторизовано записей: {total_vectorized}\n• Обработано чанков: {len(chunks)}"
            logger.info(f"✅ Векторизовано {total_vectorized} записей")
            send_admin_notification(message, chat_id)
            
            return {
                "status": "completed",
                "message": message,
                "vectorized_count": total_vectorized,
                "total_unvectorized": len(unvectorized_data)
            }
        elif not success:
            error_message = "❌ Ошибка при векторизации данных"
            logger.error(error_message)
            send_admin_notification(error_message, chat_id)
            
            return {
                "status": "error",
                "message": error_message,
                "vectorized_count": 0,
                "total_unvectorized": len(unvectorized_data)
            }
        else:
            message = "⚠️ Нет данных для векторизации"
            logger.warning(message)
            send_admin_notification(message, chat_id)
            
            return {
                "status": "no_data",
                "message": message,
                "vectorized_count": 0,
                "total_unvectorized": 0
            }
            
    except Exception as e:
        error_message = f"❌ Ошибка при векторизации: {str(e)}"
        logger.error(error_message)
        send_admin_notification(error_message, chat_id)
        
        return {
            "status": "error",
            "message": error_message,
            "vectorized_count": 0,
            "total_unvectorized": 0
        }

def get_vectorization_status(task_id: str):
    """Получает статус задачи векторизации"""
    try:
        task = celery_app.AsyncResult(task_id)
        if task.ready():
            result = task.result
            return {
                "task_id": task_id,
                "status": result.get("status", "unknown"),
                "message": result.get("message", ""),
                "vectorized_count": result.get("vectorized_count", 0),
                "total_unvectorized": result.get("total_unvectorized", 0)
            }
        else:
            return {
                "task_id": task_id,
                "status": "running",
                "message": "Векторизация в процессе",
                "vectorized_count": 0,
                "total_unvectorized": 0
            }
    except Exception as e:
        logger.error(f"Ошибка при получении статуса задачи: {e}")
        return {
            "task_id": task_id,
            "status": "error",
            "message": f"Ошибка: {str(e)}",
            "vectorized_count": 0,
            "total_unvectorized": 0
        } 