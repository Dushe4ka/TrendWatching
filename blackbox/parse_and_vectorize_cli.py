import os
import requests
from dotenv import load_dotenv
from vector_store import VectorStore
from database import get_sources, db
import asyncio

# Загружаем переменные окружения
load_dotenv()

from logger_config import setup_logger

# Настраиваем логгер
logger = setup_logger("parse_and_vectorize")

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")

def call_auth_service_parsing(limit=100):
    """Вызывает парсинг через микросервис auth_tg_service"""
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/parsing/parse_all_sources",
            json={"limit": limit},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Парсинг запущен через микросервис: {result}")
            return result
        else:
            logger.error(f"Ошибка при вызове микросервиса: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Ошибка при вызове микросервиса: {e}")
        return None

def start_parsing_after_csv_upload(new_sources=None):
    """Запускает парсинг через микросервис после загрузки CSV файла"""
    try:
        logger.info("Запуск парсинга через микросервис auth_tg_service")
        result = call_auth_service_parsing(limit=100)
        
        if result:
            return [{"status": "✅ Парсинг запущен через микросервис", "task_id": result.get("task_id")}]
        else:
            return [{"status": "❌ Ошибка при запуске парсинга через микросервис"}]
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {str(e)}")
        return [{"status": f"❌ Ошибка: {str(e)}"}]

def main():
    logger.info("--- Запуск CLI-парсинга и векторизации источников ---")
    sources = get_sources()
    total_sources = len(sources)
    vectorized_count = 0

    # Запускаем парсинг через микросервис
    parsing_result = call_auth_service_parsing(limit=100)
    if not parsing_result:
        logger.error("Не удалось запустить парсинг через микросервис")
        return

    # Ждем немного для завершения парсинга
    logger.info("Ожидание завершения парсинга...")
    import time
    time.sleep(10)

    # Теперь данные должны быть сохранены, можно векторизовать
    not_vectorized = list(db.parsed_data.find({"vectorized": False}))

    vector_store = VectorStore()
    success = vector_store.add_materials(not_vectorized)
    if success:
        vectorized_count = len(not_vectorized)
        db.parsed_data.update_many(
            {"_id": {"$in": [x["_id"] for x in not_vectorized]}},
            {"$set": {"vectorized": True}}
        )

    # Формируем отчет
    result_message = (
        f"✅ Задача завершена\n"
        f"• Источников: {total_sources}\n"
        f"• Парсинг запущен через микросервис\n"
        f"• Векторизовано: {vectorized_count}\n"
    )
    logger.info(result_message)

if __name__ == "__main__":
    main() 