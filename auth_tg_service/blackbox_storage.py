import motor.motor_asyncio
from config import BLACKBOX_MONGO_URI, BLACKBOX_DB
from bson import ObjectId
import logging

log = logging.getLogger(__name__)

# Глобальный клиент для blackbox (работает хорошо на Linux с prefork pool)
blackbox_client = motor.motor_asyncio.AsyncIOMotorClient(BLACKBOX_MONGO_URI)
blackbox_db = blackbox_client[BLACKBOX_DB]

async def get_new_channels(limit=1000):
    """
    Получить новые каналы из blackbox sources коллекции
    """
    sources_collection = blackbox_db["sources"]
    
    # Получаем каналы, которые еще не привязаны к сессиям
    # или имеют статус "new"
    cursor = sources_collection.find({
        "$or": [
            {"session_id": {"$exists": False}},
            {"status": "new"}
        ]
    }).limit(limit)
    
    return await cursor.to_list(length=limit)

async def get_all_channels(limit=1000):
    """
    Получить все каналы из blackbox sources коллекции
    """
    sources_collection = blackbox_db["sources"]
    
    # Получаем все каналы без фильтрации
    cursor = sources_collection.find({}).limit(limit)
    
    return await cursor.to_list(length=limit)

async def mark_channel_assigned(source_id, session_id):
    """
    Отметить канал как назначенный к сессии
    """
    sources_collection = blackbox_db["sources"]
    
    # Если source_id - строка, конвертируем в ObjectId
    if isinstance(source_id, str):
        source_id = ObjectId(source_id)
    
    result = await sources_collection.update_one(
        {"_id": source_id},
        {
            "$set": {
                "session_id": session_id,
                "status": "assigned"
            }
        }
    )
    return result.modified_count > 0 