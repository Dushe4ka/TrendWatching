#!/usr/bin/env python3
"""
Тест динамических клавиатур с реальными данными
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_dynamic_keyboards():
    """Тестирование динамических клавиатур с реальными данными"""
    print("🔍 Тест динамических клавиатур с реальными данными")
    print("=" * 60)
    
    try:
        from bot.keyboards.inline_keyboards import get_dynamic_main_menu_keyboard, get_admin_main_menu_keyboard
        from role_model.mongodb_provider import MongoDBRoleProvider
        from bot.utils.misc import is_admin_from_env
        
        # Инициализируем провайдер ролей
        role_provider = MongoDBRoleProvider()
        
        # Получаем все роли из базы
        print("📋 Получаем роли из базы данных...")
        roles = await role_provider.get_all_roles()
        
        if not roles:
            print("❌ Роли не найдены в базе данных")
            return
        
        print(f"✅ Найдено {len(roles)} ролей:")
        for role in roles:
            print(f"   🏷️ {role.name}: {role.description}")
        
        print("\n" + "=" * 60)
        
        # Тестируем клавиатуры для каждой роли
        for role in roles:
            print(f"\n🎯 Тест роли '{role.name}':")
            print(f"   Описание: {role.description}")
            print(f"   Права: {role.permissions}")
            
            # Создаем клавиатуру для этой роли
            keyboard = get_dynamic_main_menu_keyboard(role.permissions)
            
            print(f"   Клавиатура:")
            for i, row in enumerate(keyboard.inline_keyboard):
                for j, button in enumerate(row):
                    print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print("\n" + "=" * 60)
        
        # Тест клавиатуры администратора
        print(f"\n🔧 Тест клавиатуры администратора:")
        admin_keyboard = get_admin_main_menu_keyboard()
        print(f"   Клавиатура администратора:")
        for i, row in enumerate(admin_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print("\n" + "=" * 60)
        
        # Тест с пустыми правами
        print(f"\n❌ Тест с пустыми правами:")
        empty_permissions = {
            "can_access_sources": False,
            "can_access_analysis": False,
            "can_access_subscriptions": False,
            "can_manage_roles": False,
            "can_manage_users": False,
            "can_manage_telegram_auth": False
        }
        empty_keyboard = get_dynamic_main_menu_keyboard(empty_permissions)
        print(f"   Клавиатура без прав:")
        for i, row in enumerate(empty_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print("\n✅ Тестирование завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def test_user_access_simulation():
    """Симуляция проверки доступа пользователей"""
    print("\n👥 Симуляция проверки доступа пользователей")
    print("=" * 60)
    
    try:
        from bot.utils.misc import is_admin_from_env
        
        # Тестовые пользователи
        test_users = [
            {"id": 1395854084, "username": "admin_user", "role": "admin"},
            {"id": 5032415442, "username": "SHIFYuu", "role": "tester"},
            {"id": 123456789, "username": "analyst_user", "role": "analyst"},
            {"id": 987654321, "username": "viewer_user", "role": "viewer"},
            {"id": 555666777, "username": "no_role_user", "role": None}
        ]
        
        for user in test_users:
            print(f"\n👤 Пользователь: @{user['username']} (ID: {user['id']})")
            
            # Проверяем, является ли администратором
            is_admin = is_admin_from_env(user['id'])
            if is_admin:
                print(f"   🔧 Администратор (ADMIN_ID) - полная клавиатура")
                continue
            
            # Проверяем роль
            if user['role']:
                print(f"   🏷️ Роль: {user['role']}")
                
                # Получаем права роли
                from role_model.mongodb_provider import MongoDBRoleProvider
                role_provider = MongoDBRoleProvider()
                role_permissions = await role_provider.get_role_permissions(user['role'])
                
                if role_permissions:
                    print(f"   ✅ Права найдены: {role_permissions.permissions}")
                    
                    # Создаем клавиатуру
                    from bot.keyboards.inline_keyboards import get_dynamic_main_menu_keyboard
                    keyboard = get_dynamic_main_menu_keyboard(role_permissions.permissions)
                    
                    print(f"   📱 Клавиатура:")
                    for i, row in enumerate(keyboard.inline_keyboard):
                        for j, button in enumerate(row):
                            print(f"     [{i}][{j}]: {button.text}")
                else:
                    print(f"   ❌ Роль '{user['role']}' не найдена в базе")
            else:
                print(f"   ⚠️ Роль не назначена")
                
                # Клавиатура без прав
                from bot.keyboards.inline_keyboards import get_dynamic_main_menu_keyboard
                empty_permissions = {
                    "can_access_sources": False,
                    "can_access_analysis": False,
                    "can_access_subscriptions": False,
                    "can_manage_roles": False,
                    "can_manage_users": False,
                    "can_manage_telegram_auth": False
                }
                keyboard = get_dynamic_main_menu_keyboard(empty_permissions)
                
                print(f"   📱 Клавиатура (без прав):")
                for i, row in enumerate(keyboard.inline_keyboard):
                    for j, button in enumerate(row):
                        print(f"     [{i}][{j}]: {button.text}")
        
        print("\n✅ Симуляция завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования динамических клавиатур")
    print("=" * 60)
    
    await test_dynamic_keyboards()
    await test_user_access_simulation()
    
    print("\n🏁 Все тесты завершены")


if __name__ == "__main__":
    asyncio.run(main()) 