#!/usr/bin/env python3
"""
Тест для проверки пользователя с ID 5032415442
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_user_id_5032415442():
    """Тестирование пользователя с ID 5032415442"""
    print("🔍 Тестирование пользователя с ID 5032415442")
    print("=" * 60)
    
    user_id = 5032415442
    
    try:
        from role_model.lark_provider import LarkUserProvider
        from config import get_role_system_config
        
        # Получаем конфигурацию
        role_config = get_role_system_config()
        lark_config = role_config["lark"]
        
        # Создаем провайдер
        user_provider = LarkUserProvider(
            app_id=lark_config["app_id"],
            app_secret=lark_config["app_secret"],
            table_app_id=lark_config["table_app_id"],
            table_id=lark_config["table_id"]
        )
        
        print("✅ LarkUserProvider создан")
        print()
        
        # Тест 1: Проверяем get_user_info
        print(f"1️⃣ Проверка get_user_info для user_id: {user_id}")
        print("-" * 50)
        
        user_info = await user_provider.get_user_info(user_id)
        
        if user_info:
            print(f"✅ Пользователь найден:")
            print(f"   - User ID: {user_info.user_id}")
            print(f"   - Username: @{user_info.telegram_username}")
            print(f"   - Имя: {user_info.employee_name}")
            print(f"   - Роль: {user_info.role}")
            print(f"   - Статус: {user_info.employee_status}")
            print(f"   - Активен: {user_info.is_active}")
        else:
            print(f"❌ Пользователь с user_id {user_id} НЕ найден")
        
        print()
        
        # Тест 2: Проверяем кэш
        print(f"2️⃣ Проверка кэша")
        print("-" * 50)
        
        print(f"🔍 Размер кэша по user_id: {len(user_provider._users_by_id_cache)}")
        print(f"🔍 Размер кэша по username: {len(user_provider._users_cache)}")
        
        if user_id in user_provider._users_by_id_cache:
            print(f"✅ Пользователь найден в кэше по user_id")
        else:
            print(f"❌ Пользователь НЕ найден в кэше по user_id")
        
        # Показываем первые 10 user_id в кэше
        user_ids = list(user_provider._users_by_id_cache.keys())[:10]
        print(f"🔍 Первые 10 user_id в кэше: {user_ids}")
        
        # Показываем первые 10 username в кэше
        usernames = list(user_provider._users_cache.keys())[:10]
        print(f"🔍 Первые 10 username в кэше: {usernames}")
        
        print()
        
        # Тест 3: Проверяем MongoDB
        print(f"3️⃣ Проверка MongoDB")
        print("-" * 50)
        
        from database import db
        
        # Ищем пользователя в коллекции users_lark
        user_doc = db.users_lark.find_one({"username": {"$exists": True}})
        
        if user_doc:
            print(f"✅ Пользователи есть в MongoDB")
            print(f"   Пример пользователя: @{user_doc.get('username', 'N/A')}")
            
            # Ищем пользователя с role = "tester"
            tester_users = list(db.users_lark.find({"role": "tester"}))
            print(f"🔍 Пользователей с ролью 'tester': {len(tester_users)}")
            
            for i, user in enumerate(tester_users):
                print(f"   {i+1}. @{user.get('username', 'N/A')} - {user.get('employee_name', 'N/A')} - {user.get('employee_status', 'N/A')}")
        else:
            print(f"❌ Пользователи НЕ найдены в MongoDB")
        
        print()
        
        # Тест 4: Проверяем через role_manager
        print(f"4️⃣ Проверка через role_manager")
        print("-" * 50)
        
        from bot.utils.misc import get_role_manager_async
        
        role_manager = await get_role_manager_async()
        if role_manager:
            print(f"✅ RoleManager получен")
            
            # Проверяем get_user_info через role_manager
            user_info_from_manager = await role_manager.get_user_info(user_id)
            
            if user_info_from_manager:
                print(f"✅ Пользователь найден через role_manager:")
                print(f"   - Username: @{user_info_from_manager.telegram_username}")
                print(f"   - Имя: {user_info_from_manager.employee_name}")
                print(f"   - Роль: {user_info_from_manager.role}")
            else:
                print(f"❌ Пользователь НЕ найден через role_manager")
        else:
            print(f"❌ RoleManager недоступен")
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования пользователя с ID 5032415442")
    print("=" * 60)
    
    await test_user_id_5032415442()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 