import os
import motor.motor_asyncio
from typing import List, Dict, Any
from bson import ObjectId
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация MongoDB - используем ту же базу данных, что и сервис авторизации
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "tg_auth_service")  # Изменено с "trendwatching" на "tg_auth_service"

# Создаем клиент MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client[DB_NAME]

async def get_unvectorized_data_async():
    """Асинхронная версия получения невекторизованных данных"""
    try:
        cursor = db.parsed_data.find({"vectorized": False})
        documents = await cursor.to_list(length=None)
        
        # Конвертируем ObjectId в строки для JSON сериализации
        for doc in documents:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
        
        return documents
    except Exception as e:
        print(f"Ошибка при получении невекторизованных данных: {e}")
        return []

async def update_vectorization_status_async(ids: List[ObjectId]):
    """Асинхронная версия обновления статуса векторизации"""
    try:
        result = await db.parsed_data.update_many(
            {"_id": {"$in": ids}},
            {"$set": {"vectorized": True}}
        )
        print(f"Обновлен статус векторизации для {result.modified_count} записей")
        return result.modified_count
    except Exception as e:
        print(f"Ошибка при обновлении статуса векторизации: {e}")
        return 0

async def get_vectorized_data_count_async():
    """Асинхронная версия получения количества векторизованных записей"""
    try:
        count = await db.parsed_data.count_documents({"vectorized": True})
        return count
    except Exception as e:
        print(f"Ошибка при получении количества векторизованных записей: {e}")
        return 0

async def get_unvectorized_data_count_async():
    """Асинхронная версия получения количества невекторизованных записей"""
    try:
        count = await db.parsed_data.count_documents({"vectorized": False})
        return count
    except Exception as e:
        print(f"Ошибка при получении количества невекторизованных записей: {e}")
        return 0 