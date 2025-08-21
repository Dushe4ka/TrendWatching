#!/usr/bin/env python3
"""
Тест для отладки проблемы с username
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_username_search():
    """Тестирование поиска пользователя по username"""
    print("🔍 Тестирование поиска пользователя по username")
    print("=" * 60)
    
    try:
        # Импортируем необходимые модули
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
        
        # Тестируем поиск конкретного пользователя
        test_usernames = [
            "alexdru",  # Из логов видно, что этот пользователь есть
            "SHIFYuu",  # Из логов видно, что этот пользователь есть
            "test_user",  # Несуществующий пользователь
        ]
        
        for username in test_usernames:
            print(f"\n🔍 Тестирование username: @{username}")
            print("-" * 40)
            
            # Ищем пользователя
            user_doc = await user_provider.get_user_by_username_from_lark(username)
            
            if user_doc:
                print(f"✅ Пользователь @{username} найден:")
                print(f"   Username: {user_doc.get('username', 'N/A')}")
                print(f"   Имя: {user_doc.get('employee_name', 'N/A')}")
                print(f"   Роль: {user_doc.get('role', 'N/A')}")
                print(f"   Статус: {user_doc.get('status', 'N/A')}")
                print(f"   Статус сотрудника: {user_doc.get('employee_status', 'N/A')}")
                
                # Тестируем проверку доступа
                print(f"\n🔍 Тестирование проверки доступа для @{username}...")
                access_granted, error_message = await user_provider.check_user_access(username)
                
                if access_granted:
                    print(f"✅ Доступ разрешен для @{username}")
                else:
                    print(f"❌ Доступ запрещен для @{username}: {error_message}")
            else:
                print(f"❌ Пользователь @{username} НЕ найден")
        
        # Показываем всех пользователей в коллекции
        print(f"\n📋 Список всех пользователей в коллекции users_lark:")
        print("-" * 60)
        
        try:
            all_users = list(user_provider.users_lark_collection.find({}))
            print(f"Всего пользователей: {len(all_users)}")
            
            # Группируем по ролям
            roles_count = {}
            for user in all_users:
                role = user.get('role', 'Не назначена')
                roles_count[role] = roles_count.get(role, 0) + 1
            
            print(f"\nРаспределение по ролям:")
            for role, count in roles_count.items():
                print(f"   {role}: {count} пользователей")
            
            # Показываем первые 10 пользователей
            print(f"\nПервые 10 пользователей:")
            for i, user in enumerate(all_users[:10]):
                username = user.get('username', 'N/A')
                name = user.get('employee_name', 'N/A')
                role = user.get('role', 'N/A')
                status = user.get('employee_status', 'N/A')
                print(f"   {i+1}. @{username} - {name} - {role} - {status}")
            
            if len(all_users) > 10:
                print(f"   ... и еще {len(all_users) - 10} пользователей")
                
        except Exception as e:
            print(f"❌ Ошибка при получении списка пользователей: {e}")
        
        print("\n✅ Тестирование завершено")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


async def test_admin_access():
    """Тестирование доступа администратора"""
    print("\n👑 Тестирование доступа администратора")
    print("=" * 60)
    
    try:
        from bot.utils.misc import is_admin
        
        # Тестируем с разными ID
        test_user_ids = [
            1395854084,  # Из логов
            5032415442,  # Из логов
            123456789,   # Тестовый ID
        ]
        
        for user_id in test_user_ids:
            print(f"\n🔍 Тестирование администратора ID: {user_id}")
            print("-" * 40)
            
            is_admin_user = await is_admin(user_id)
            
            if is_admin_user:
                print(f"✅ Пользователь ID {user_id} является администратором")
            else:
                print(f"❌ Пользователь ID {user_id} НЕ является администратором")
        
        # Проверяем переменную окружения
        admin_ids_str = os.getenv("ADMIN_ID")
        if admin_ids_str:
            print(f"\n🔧 Переменная окружения ADMIN_ID: {admin_ids_str}")
            # Разбираем строку с ID через запятую
            admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip().isdigit()]
            print(f"🔧 Список администраторов: {admin_ids}")
        else:
            print(f"\n⚠️ Переменная окружения ADMIN_ID не установлена")
        
        print("\n✅ Тестирование администратора завершено")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании администратора: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестов отладки username")
    print("=" * 80)
    
    await test_username_search()
    await test_admin_access()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 