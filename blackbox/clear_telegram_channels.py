#!/usr/bin/env python3
"""
Скрипт для очистки некорректных данных из коллекции telegram_channels
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Подключение к MongoDB
client = MongoClient(
    os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'),
    serverSelectionTimeoutMS=5000
)

db = client[os.getenv('MONGODB_DB', 'blackbox')]
telegram_channels_collection = db["telegram_channels"]

def clear_invalid_data():
    """Очищает некорректные данные из коллекции"""
    print("🧹 Начинаем очистку коллекции telegram_channels...")
    
    # Удаляем все документы с некорректными данными
    result = telegram_channels_collection.delete_many({})
    print(f"✅ Удалено {result.deleted_count} документов из коллекции")
    
    # Удаляем все индексы кроме _id_
    try:
        indexes = list(telegram_channels_collection.list_indexes())
        for index in indexes:
            if index['name'] != '_id_':
                telegram_channels_collection.drop_index(index['name'])
                print(f"🗑️ Удален индекс: {index['name']}")
    except Exception as e:
        print(f"⚠️ Ошибка при удалении индексов: {e}")
    
    print("✅ Очистка завершена. Теперь можно перезапустить бота.")

if __name__ == "__main__":
    try:
        clear_invalid_data()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        client.close() 