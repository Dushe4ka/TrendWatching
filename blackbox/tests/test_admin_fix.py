#!/usr/bin/env python3
"""
Тест для проверки исправленной логики администратора
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_admin_access():
    """Тестирование доступа администратора"""
    print("👑 Тестирование доступа администратора")
    print("=" * 60)
    
    try:
        from bot.utils.misc import is_admin, check_user_access, check_permission
        
        # Тестируем с разными ID
        test_user_ids = [
            1395854084,  # Из ADMIN_ID
            5103990965,  # Из ADMIN_ID
            5032415442,  # Не в ADMIN_ID, но есть в системе
            123456789,   # Тестовый ID
        ]
        
        for user_id in test_user_ids:
            print(f"\n🔍 Тестирование пользователя ID: {user_id}")
            print("-" * 40)
            
            # Тест 1: Проверка is_admin
            print(f"1. Проверка is_admin...")
            is_admin_user = await is_admin(user_id)
            print(f"   Результат: {'✅ Администратор' if is_admin_user else '❌ Не администратор'}")
            
            # Тест 2: Проверка check_user_access
            print(f"2. Проверка check_user_access...")
            access_granted, message, role = await check_user_access(user_id, None)  # Для админов username не нужен
            print(f"   Результат: {'✅ Доступ разрешен' if access_granted else '❌ Доступ запрещен'}")
            print(f"   Сообщение: {message}")
            print(f"   Роль: {role}")
            
            # Тест 3: Проверка check_permission
            print(f"3. Проверка check_permission (can_use_analysis)...")
            has_permission = await check_permission(user_id, "can_use_analysis")
            print(f"   Результат: {'✅ Разрешение есть' if has_permission else '❌ Разрешения нет'}")
        
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


async def test_username_access():
    """Тестирование доступа по username"""
    print("\n🔍 Тестирование доступа по username")
    print("=" * 60)
    
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
        
        # Тестируем поиск конкретного пользователя
        test_usernames = [
            "alexdru",  # Есть в системе, роль "Не назначена"
            "SHIFYuu",  # Есть в системе, роль "tester"
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
        
        print("\n✅ Тестирование username завершено")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании username: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестов исправленной логики администратора")
    print("=" * 80)
    
    await test_admin_access()
    await test_username_access()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 