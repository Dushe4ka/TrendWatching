import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv
from logger_config import setup_logger
from models import TelegramChannel, DigestSchedule, TelegramChannelWithDigests

# Настраиваем логгер
logger = setup_logger("telegram_channels_service")

# Загружаем переменные окружения
load_dotenv()

# Подключение к MongoDB
try:
    client = MongoClient(
        os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'),
        serverSelectionTimeoutMS=5000
    )
    client.admin.command('ping')
    logger.info("✅ MongoDB подключена для telegram_channels_service")
except Exception as e:
    logger.error(f"❌ Ошибка подключения к MongoDB: {e}")
    raise

db = client[os.getenv('MONGODB_DB', 'blackbox')]

# Создаем коллекцию для Telegram каналов
telegram_channels_collection = db["telegram_channels"]

# Удаляем старые неправильные индексы
try:
    # Получаем список всех индексов
    indexes = list(telegram_channels_collection.list_indexes())
    for index in indexes:
        if index['name'] != '_id_':  # Не удаляем основной индекс _id
            telegram_channels_collection.drop_index(index['name'])
            logger.info(f"Удален старый индекс: {index['name']}")
except Exception as e:
    logger.warning(f"Не удалось удалить старые индексы: {e}")

# Создаем правильные индексы
try:
    # Уникальный индекс по ID канала
    telegram_channels_collection.create_index("id", unique=True, name="channel_id_unique")
    # Индекс по username (может быть None, поэтому sparse=True)
    telegram_channels_collection.create_index("username", sparse=True, name="channel_username")
    logger.info("✅ Индексы для telegram_channels созданы успешно")
except Exception as e:
    logger.error(f"❌ Ошибка при создании индексов: {e}")
    raise

class TelegramChannelsService:
    """Сервис для управления Telegram каналами и дайджестами"""
    
    def __init__(self):
        self.collection = telegram_channels_collection
    
    def add_channel(self, channel_data: Dict[str, Any]) -> bool:
        """
        Добавляет новый Telegram канал
        
        Args:
            channel_data: Данные канала (id, title, username, type)
            
        Returns:
            bool: True если успешно добавлен, False в противном случае
        """
        try:
            # Проверяем валидность данных
            if not channel_data.get("id"):
                logger.error("ID канала не может быть пустым")
                return False
                
            if not channel_data.get("title"):
                logger.error("Название канала не может быть пустым")
                return False
            
            # Проверяем, существует ли уже канал с таким ID
            existing_channel = self.collection.find_one({"id": channel_data["id"]})
            if existing_channel:
                logger.info(f"Канал с ID {channel_data['id']} уже существует")
                return True  # Считаем это успехом
            
            # Создаем новый канал
            channel = {
                "id": channel_data["id"],
                "title": channel_data["title"],
                "username": channel_data.get("username"),
                "type": channel_data.get("type", "channel"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "digests": []  # Пустой список дайджестов
            }
            
            logger.info(f"Попытка сохранения канала: {channel}")
            
            result = self.collection.insert_one(channel)
            if result.inserted_id:
                logger.info(f"Канал {channel_data['title']} успешно добавлен с ID: {result.inserted_id}")
                return True
            else:
                logger.error("Ошибка при добавлении канала")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при добавлении канала: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_all_channels(self) -> List[TelegramChannel]:
        """
        Получает все Telegram каналы
        
        Returns:
            List[TelegramChannel]: Список каналов
        """
        try:
            channels = list(self.collection.find({}, {"_id": 0, "digests": 0}))
            return [TelegramChannel(**channel) for channel in channels]
        except Exception as e:
            logger.error(f"Ошибка при получении каналов: {str(e)}")
            return []
    
    def get_channel_by_id(self, channel_id: int) -> Optional[TelegramChannelWithDigests]:
        """
        Получает канал по ID с дайджестами
        
        Args:
            channel_id: ID канала
            
        Returns:
            Optional[TelegramChannelWithDigests]: Канал с дайджестами или None
        """
        try:
            channel_data = self.collection.find_one({"id": channel_id})
            if not channel_data:
                return None
            
            # Преобразуем дайджесты
            digests = []
            for digest_data in channel_data.get("digests", []):
                digest = DigestSchedule(
                    id=digest_data["id"],
                    category=digest_data["category"],
                    time=digest_data["time"],
                    is_active=digest_data.get("is_active", True),
                    created_at=digest_data.get("created_at", datetime.utcnow()),
                    updated_at=digest_data.get("updated_at", datetime.utcnow())
                )
                digests.append(digest)
            
            # Создаем объект канала
            channel = TelegramChannel(
                id=channel_data["id"],
                title=channel_data["title"],
                username=channel_data.get("username"),
                type=channel_data.get("type", "channel"),
                created_at=channel_data.get("created_at", datetime.utcnow()),
                updated_at=channel_data.get("updated_at", datetime.utcnow())
            )
            
            return TelegramChannelWithDigests(channel=channel, digests=digests)
            
        except Exception as e:
            logger.error(f"Ошибка при получении канала {channel_id}: {str(e)}")
            return None
    
    def add_digest_to_channel(self, channel_id: int, category: str, time: str) -> bool:
        """
        Добавляет дайджест к каналу и автоматически добавляет его в планировщик
        
        Args:
            channel_id: ID канала
            category: Категория дайджеста
            time: Время отправки в формате HH:MM
            
        Returns:
            bool: True если успешно добавлен, False в противном случае
        """
        try:
            # Проверяем формат времени
            try:
                hour, minute = map(int, time.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("Некорректное время")
            except ValueError:
                logger.error(f"Некорректный формат времени: {time}")
                return False
            
            # Создаем новый дайджест
            digest_id = str(uuid.uuid4())
            digest = {
                "id": digest_id,
                "category": category,
                "time": time,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Добавляем дайджест к каналу
            result = self.collection.update_one(
                {"id": channel_id},
                {
                    "$push": {"digests": digest},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Дайджест для категории {category} добавлен к каналу {channel_id}")
                
                return True
            else:
                logger.error(f"Канал с ID {channel_id} не найден")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при добавлении дайджеста: {str(e)}")
            return False
    
    def update_digest(self, channel_id: int, digest_id: str, updates: Dict[str, Any]) -> bool:
        """
        Обновляет дайджест и автоматически обновляет планировщик при изменении времени
        
        Args:
            channel_id: ID канала
            digest_id: ID дайджеста
            updates: Словарь с обновлениями
            
        Returns:
            bool: True если успешно обновлен, False в противном случае
        """
        try:
            # Проверяем формат времени, если оно обновляется
            if "time" in updates:
                try:
                    hour, minute = map(int, updates["time"].split(':'))
                    if not (0 <= hour <= 23 and 0 <= minute <= 59):
                        raise ValueError("Некорректное время")
                except ValueError:
                    logger.error(f"Некорректный формат времени: {updates['time']}")
                    return False
            
            # Обновляем дайджест
            update_data = {
                f"digests.$.{key}": value 
                for key, value in updates.items()
            }
            update_data["digests.$.updated_at"] = datetime.utcnow()
            
            logger.info(f"Обновление дайджеста {digest_id}: {update_data}")
            
            # Проверяем, существует ли дайджест
            existing_digest = self.collection.find_one(
                {"id": channel_id, "digests.id": digest_id},
                {"digests.$": 1}
            )
            logger.info(f"Существующий дайджест: {existing_digest}")
            
            result = self.collection.update_one(
                {
                    "id": channel_id,
                    "digests.id": digest_id
                },
                {
                    "$set": {
                        **update_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Результат обновления: modified_count={result.modified_count}, matched_count={result.matched_count}")
            
            if result.modified_count > 0:
                logger.info(f"Дайджест {digest_id} обновлен в канале {channel_id}")
                
                return True
            else:
                logger.error(f"Дайджест {digest_id} не найден в канале {channel_id}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении дайджеста: {str(e)}")
            return False
    
    def delete_digest(self, channel_id: int, digest_id: str) -> bool:
        """
        Удаляет дайджест из канала и автоматически удаляет его из планировщика
        
        Args:
            channel_id: ID канала
            digest_id: ID дайджеста
            
        Returns:
            bool: True если успешно удален, False в противном случае
        """
        try:
            result = self.collection.update_one(
                {"id": channel_id},
                {
                    "$pull": {"digests": {"id": digest_id}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"Дайджест {digest_id} удален из канала {channel_id}")
                
                return True
            else:
                logger.error(f"Дайджест {digest_id} в канале {channel_id} не найден")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при удалении дайджеста: {str(e)}")
            return False
    
    def get_active_digests(self) -> List[Dict[str, Any]]:
        """
        Получает все активные дайджесты для планировщика
        
        Returns:
            List[Dict[str, Any]]: Список активных дайджестов
        """
        try:
            pipeline = [
                {"$unwind": "$digests"},
                {"$match": {"digests.is_active": True}},
                {"$project": {
                    "channel_id": "$id",
                    "channel_title": "$title",
                    "digest_id": "$digests.id",
                    "category": "$digests.category",
                    "time": "$digests.time"
                }}
            ]
            
            active_digests = list(self.collection.aggregate(pipeline))
            logger.info(f"Найдено {len(active_digests)} активных дайджестов")
            return active_digests
            
        except Exception as e:
            logger.error(f"Ошибка при получении активных дайджестов: {str(e)}")
            return []

# Создаем глобальный экземпляр сервиса
telegram_channels_service = TelegramChannelsService() 