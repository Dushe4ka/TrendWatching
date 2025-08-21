#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функционала Telegram каналов и дайджестов
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
load_dotenv()

def test_telegram_channels_service():
    """Тестирует сервис Telegram каналов"""
    print("🧪 Тестирование сервиса Telegram каналов...")
    
    try:
        from telegram_channels_service import telegram_channels_service
        
        # Тест 1: Получение всех каналов
        print("📢 Тест 1: Получение всех каналов...")
        channels = telegram_channels_service.get_all_channels()
        print(f"   Найдено каналов: {len(channels)}")
        
        # Тест 2: Добавление тестового канала
        print("📢 Тест 2: Добавление тестового канала...")
        test_channel = {
            "id": 999999999,
            "title": "Тестовый канал",
            "username": "test_channel",
            "type": "channel"
        }
        
        success = telegram_channels_service.add_channel(test_channel)
        print(f"   Канал добавлен: {'✅' if success else '❌'}")
        
        # Тест 3: Получение канала по ID
        print("📢 Тест 3: Получение канала по ID...")
        channel_info = telegram_channels_service.get_channel_by_id(999999999)
        if channel_info:
            print(f"   Канал найден: {channel_info.channel.title}")
        else:
            print("   ❌ Канал не найден")
        
        # Тест 4: Добавление дайджеста
        print("📢 Тест 4: Добавление дайджеста...")
        success = telegram_channels_service.add_digest_to_channel(
            999999999, "Технологии", "14:30"
        )
        print(f"   Дайджест добавлен: {'✅' if success else '❌'}")
        
        # Тест 5: Получение активных дайджестов
        print("📢 Тест 5: Получение активных дайджестов...")
        active_digests = telegram_channels_service.get_active_digests()
        print(f"   Активных дайджестов: {len(active_digests)}")
        
        # Тест 6: Обновление дайджеста
        print("📢 Тест 6: Обновление дайджеста...")
        if active_digests:
            digest_id = active_digests[0]["digest_id"]
            success = telegram_channels_service.update_digest(
                999999999, digest_id, {"time": "15:00"}
            )
            print(f"   Дайджест обновлен: {'✅' if success else '❌'}")
        
        # Тест 7: Удаление дайджеста
        print("📢 Тест 7: Удаление дайджеста...")
        if active_digests:
            digest_id = active_digests[0]["digest_id"]
            success = telegram_channels_service.delete_digest(999999999, digest_id)
            print(f"   Дайджест удален: {'✅' if success else '❌'}")
        
        print("✅ Тестирование сервиса завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()

def test_models():
    """Тестирует модели данных"""
    print("🧪 Тестирование моделей данных...")
    
    try:
        from models import TelegramChannel, DigestSchedule, TelegramChannelWithDigests
        
        # Тест 1: Создание канала
        print("📋 Тест 1: Создание модели канала...")
        channel = TelegramChannel(
            id=123456789,
            title="Тестовый канал",
            username="test_channel",
            type="channel"
        )
        print(f"   Канал создан: {channel.title}")
        
        # Тест 2: Создание дайджеста
        print("📋 Тест 2: Создание модели дайджеста...")
        digest = DigestSchedule(
            id="test-uuid",
            category="Технологии",
            time="14:30"
        )
        print(f"   Дайджест создан: {digest.category} - {digest.time}")
        
        # Тест 3: Создание канала с дайджестами
        print("📋 Тест 3: Создание канала с дайджестами...")
        channel_with_digests = TelegramChannelWithDigests(
            channel=channel,
            digests=[digest]
        )
        print(f"   Канал с дайджестами создан: {len(channel_with_digests.digests)} дайджестов")
        
        print("✅ Тестирование моделей завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании моделей: {str(e)}")
        import traceback
        traceback.print_exc()

def test_database_connection():
    """Тестирует подключение к базе данных"""
    print("🧪 Тестирование подключения к базе данных...")
    
    try:
        from database import db
        
        # Проверяем подключение
        result = db.command("ping")
        print(f"   Подключение к MongoDB: {'✅' if result else '❌'}")
        
        # Проверяем коллекцию telegram_channels
        collections = db.list_collection_names()
        if "telegram_channels" in collections:
            print("   Коллекция telegram_channels: ✅")
        else:
            print("   Коллекция telegram_channels: ❌ (не найдена)")
        
        print("✅ Тестирование базы данных завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании базы данных: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования функционала Telegram каналов...\n")
    
    # Проверяем переменные окружения
    required_vars = ["MONGODB_URI", "MONGODB_DB"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("Создайте файл .env с необходимыми переменными")
        return
    
    print(f"📊 Конфигурация:")
    print(f"   MongoDB URI: {os.getenv('MONGODB_URI')}")
    print(f"   MongoDB DB: {os.getenv('MONGODB_DB')}")
    print()
    
    # Запускаем тесты
    test_database_connection()
    print()
    
    test_models()
    print()
    
    test_telegram_channels_service()
    print()
    
    print("🎉 Все тесты завершены!")

if __name__ == "__main__":
    main() 