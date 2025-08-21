#!/usr/bin/env python3
"""
Скрипт для проверки доступа конкретных пользователей
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_specific_users():
    """Тестирование доступа конкретных пользователей"""
    print("🔍 Тестирование доступа конкретных пользователей")
    print("=" * 80)
    
    # Список пользователей для тестирования
    test_usernames = [
        "SHIFYuu",
        "Lavkaaa_helper"
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
        
        for username in test_usernames:
            print(f"🔍 Тестирование пользователя: @{username}")
            print("-" * 60)
            
            # Шаг 1: Поиск пользователя в системе
            print(f"1️⃣ Поиск пользователя @{username} в системе...")
            user_doc = await user_provider.get_user_by_username_from_lark(username)
            
            if not user_doc:
                print(f"❌ ОШИБКА: Пользователь @{username} НЕ найден в системе")
                print(f"   Причина: Пользователь отсутствует в коллекции users_lark")
                print(f"   Решение: Добавить пользователя в Lark Base или проверить синхронизацию")
                print()
                continue
            
            print(f"✅ Пользователь @{username} найден в системе")
            print(f"   📋 Данные пользователя:")
            print(f"      - Username: {user_doc.get('username', 'N/A')}")
            print(f"      - Имя: {user_doc.get('employee_name', 'N/A')}")
            print(f"      - Роль: {user_doc.get('role', 'N/A')}")
            print(f"      - Статус: {user_doc.get('status', 'N/A')}")
            print(f"      - Статус сотрудника: {user_doc.get('employee_status', 'N/A')}")
            print()
            
            # Шаг 2: Проверка доступа
            print(f"2️⃣ Проверка доступа для @{username}...")
            access_granted, error_message = await user_provider.check_user_access(username)
            
            if access_granted:
                print(f"✅ ДОСТУП РАЗРЕШЕН для @{username}")
                print(f"   🎉 Пользователь может использовать бота")
            else:
                print(f"❌ ДОСТУП ЗАПРЕЩЕН для @{username}")
                print(f"   🚫 Причина: {error_message}")
                
                # Детальный анализ ошибки
                print(f"   🔍 Детальный анализ:")
                
                # Проверка статуса сотрудника
                employee_status = user_doc.get('employee_status', '')
                if employee_status != 'Работает':
                    print(f"      ❌ Статус сотрудника: '{employee_status}' (должен быть 'Работает')")
                else:
                    print(f"      ✅ Статус сотрудника: '{employee_status}' - корректный")
                
                # Проверка роли
                role = user_doc.get('role', '')
                if role == 'Не назначена':
                    print(f"      ❌ Роль: '{role}' (роль не назначена)")
                else:
                    print(f"      ✅ Роль: '{role}' - назначена")
                    
                    # Проверка наличия роли в системе
                    from role_model.mongodb_provider import MongoDBRoleProvider
                    role_provider = MongoDBRoleProvider()
                    role_exists = await role_provider.role_exists(role)
                    
                    if role_exists:
                        print(f"      ✅ Роль '{role}' найдена в системе ролей")
                    else:
                        print(f"      ❌ Роль '{role}' НЕ найдена в системе ролей")
                        print(f"         Решение: Зарегистрировать роль '{role}' в боте")
            
            print()
            print("=" * 80)
            print()
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


async def test_admin_access():
    """Тестирование доступа администраторов"""
    print("👑 Тестирование доступа администраторов")
    print("=" * 80)
    
    try:
        from bot.utils.misc import is_admin, check_user_access
        
        # Проверяем переменную окружения
        admin_ids_str = os.getenv("ADMIN_ID")
        if admin_ids_str:
            admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip().isdigit()]
            print(f"🔧 Администраторы из ADMIN_ID: {admin_ids}")
            
            for admin_id in admin_ids:
                print(f"\n🔍 Тестирование администратора ID: {admin_id}")
                print("-" * 40)
                
                # Проверка is_admin
                is_admin_user = await is_admin(admin_id)
                print(f"   is_admin({admin_id}): {'✅ Да' if is_admin_user else '❌ Нет'}")
                
                # Проверка check_user_access
                access_granted, message, role = await check_user_access(admin_id, None)  # Для админов username не нужен
                print(f"   check_user_access({admin_id}): {'✅ Доступ разрешен' if access_granted else '❌ Доступ запрещен'}")
                print(f"   Сообщение: {message}")
                print(f"   Роль: {role}")
        else:
            print("⚠️ Переменная окружения ADMIN_ID не установлена")
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании администраторов: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования конкретных пользователей")
    print("=" * 80)
    
    await test_specific_users()
    await test_admin_access()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 