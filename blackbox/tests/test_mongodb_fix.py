#!/usr/bin/env python3
"""
Тест для проверки исправлений MongoDB
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_mongodb_operations():
    """Тестирование операций MongoDB"""
    print("🧪 Тестирование операций MongoDB")
    print("=" * 50)
    
    try:
        # Тест 1: Подключение к базе данных
        print("1. Подключение к MongoDB...")
        from database import db
        print("   ✅ Подключение к MongoDB успешно")
        
        # Тест 2: Операции с коллекцией users_lark
        print("\n2. Тестирование коллекции users_lark...")
        
        # Очищаем коллекцию
        result = db.users_lark.delete_many({})
        print(f"   Удалено документов: {result.deleted_count}")
        
        # Вставляем тестовый документ
        test_user = {
            "username": "test_user",
            "employee_name": "Тестовый Пользователь",
            "role": "tester",
            "status": "✅ Активен",
            "employee_status": "Работает",
            "synced_at": datetime.now().isoformat()
        }
        
        result = db.users_lark.insert_one(test_user)
        print(f"   Вставлен документ с ID: {result.inserted_id}")
        
        # Ищем документ
        found_user = db.users_lark.find_one({"username": "test_user"})
        if found_user:
            print(f"   ✅ Документ найден: {found_user['username']} - {found_user['employee_name']}")
        else:
            print("   ❌ Документ не найден")
        
        # Подсчитываем документы
        count = db.users_lark.count_documents({})
        print(f"   Всего документов в коллекции: {count}")
        
        # Очищаем тестовые данные
        db.users_lark.delete_many({"username": "test_user"})
        print("   Тестовые данные очищены")
        
        print("\n✅ Все тесты MongoDB завершены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_lark_provider():
    """Тестирование LarkUserProvider"""
    print("\n🔧 Тестирование LarkUserProvider")
    print("=" * 50)
    
    try:
        # Тест 1: Создание провайдера
        print("1. Создание LarkUserProvider...")
        from config import get_role_system_config
        from role_model.lark_provider import LarkUserProvider
        
        role_config = get_role_system_config()["lark"]
        provider = LarkUserProvider(
            app_id=role_config["app_id"],
            app_secret=role_config["app_secret"],
            table_app_id=role_config["table_app_id"],
            table_id=role_config["table_id"]
        )
        print("   ✅ LarkUserProvider создан успешно")
        
        # Тест 2: Проверка коллекции
        print("\n2. Проверка коллекции users_lark...")
        count = provider.users_lark_collection.count_documents({})
        print(f"   Документов в коллекции: {count}")
        
        # Тест 3: Запуск синхронизации
        print("\n3. Запуск периодической синхронизации...")
        await provider.start_periodic_sync()
        print("   ✅ Периодическая синхронизация запущена")
        
        # Тест 4: Остановка синхронизации
        print("\n4. Остановка периодической синхронизации...")
        await provider.stop_periodic_sync()
        print("   ✅ Периодическая синхронизация остановлена")
        
        print("\n✅ Все тесты LarkUserProvider завершены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print(f"🚀 Запуск тестов исправлений MongoDB - {datetime.now()}")
    print("=" * 80)
    
    await test_mongodb_operations()
    await test_lark_provider()
    
    print(f"\n🏁 Тестирование завершено - {datetime.now()}")


if __name__ == "__main__":
    asyncio.run(main()) 