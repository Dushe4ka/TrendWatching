import motor.motor_asyncio
from config import MONGO_URI, MONGO_DB
import logging

log = logging.getLogger(__name__)

# Глобальный клиент (работает хорошо на Linux с prefork pool)
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB]

sessions_collection = db["sessions"]
channel_bindings_collection = db["channel_bindings"]

async def create_session(session_data: dict):
    return await sessions_collection.insert_one(session_data)

async def get_sessions():
    """Получить все сессии"""
    return await sessions_collection.find().to_list(length=1000)

async def get_session_by_phone(phone_number: str):
    return await sessions_collection.find_one({"phone_number": phone_number})

async def get_session_by_id(session_id: str):
    """Получить сессию по session_id"""
    return await sessions_collection.find_one({"session_id": session_id})

async def update_session(session_id: str, update_data: dict):
    return await sessions_collection.update_one({"session_id": session_id}, {"$set": update_data})

async def update_session_by_phone(phone_number: str, update_data: dict):
    """Обновить сессию по номеру телефона"""
    result = await sessions_collection.update_one(
        {"phone_number": phone_number},
        {"$set": update_data}
    )
    return result.modified_count > 0

async def create_channel_binding(binding_data: dict):
    return await channel_bindings_collection.insert_one(binding_data)

async def get_channel_bindings(session_id: str):
    return await channel_bindings_collection.find({"session_id": session_id}).to_list(length=1000) 