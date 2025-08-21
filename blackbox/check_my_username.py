#!/usr/bin/env python3
"""
Скрипт для проверки username пользователя
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def check_username_in_system():
    """Проверка username в системе"""
    print("🔍 Проверка username в системе")
    print("=" * 50)
    
    # Попробуем разные варианты username
    possible_usernames = [
        "SHIFYuu",
        "shifyuu", 
        "Shifyuu",
        "SHIFYUU",
        "Lavkaaa_helper",
        "lavkaaa_helper",
        "LavkaaaHelper",
        "alexdru",
        "Alexdru",
        "ALEXDRU"
    ]
    
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
        
        found_users = []
        
        for username in possible_usernames:
            print(f"🔍 Проверяем: '{username}'")
            
            # Ищем пользователя
            user_doc = await user_provider.get_user_by_username_from_lark(username)
            
            if user_doc:
                print(f"✅ НАЙДЕН: '{username}'")
                print(f"   - Имя: {user_doc.get('employee_name', 'N/A')}")
                print(f"   - Роль: {user_doc.get('role', 'N/A')}")
                print(f"   - Статус: {user_doc.get('employee_status', 'N/A')}")
                
                # Проверяем доступ
                access_granted, error_message = await user_provider.check_user_access(username)
                print(f"   - Доступ: {'✅ Разрешен' if access_granted else '❌ Запрещен'}")
                if not access_granted:
                    print(f"   - Причина: {error_message}")
                
                found_users.append({
                    'username': username,
                    'user_doc': user_doc,
                    'access_granted': access_granted,
                    'error_message': error_message
                })
            else:
                print(f"❌ НЕ найден: '{username}'")
            
            print()
        
        # Выводим итоги
        print("📊 ИТОГИ:")
        print("=" * 50)
        
        if found_users:
            print(f"✅ Найдено пользователей: {len(found_users)}")
            for user in found_users:
                status = "✅ Доступ разрешен" if user['access_granted'] else "❌ Доступ запрещен"
                print(f"   - @{user['username']}: {status}")
                if not user['access_granted']:
                    print(f"     Причина: {user['error_message']}")
        else:
            print("❌ Пользователи не найдены")
            print("   Возможные причины:")
            print("   - Username отличается от указанных")
            print("   - Пользователь не добавлен в Lark Base")
            print("   - Проблема с синхронизацией")
        
        # Показываем всех пользователей с ролью tester
        print("\n🔍 Все пользователи с ролью 'tester':")
        print("-" * 30)
        
        from database import db
        tester_users = db.users_lark.find({"role": "tester"})
        count = 0
        for user in tester_users:
            count += 1
            print(f"   {count}. @{user.get('username', 'N/A')} - {user.get('employee_name', 'N/A')} - {user.get('employee_status', 'N/A')}")
        
        if count == 0:
            print("   Нет пользователей с ролью 'tester'")
    
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Проверка username в системе")
    print("=" * 50)
    
    await check_username_in_system()
    
    print("\n🏁 Проверка завершена")


if __name__ == "__main__":
    asyncio.run(main()) 