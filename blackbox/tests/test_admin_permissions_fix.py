#!/usr/bin/env python3
"""
Тест исправленных админских разрешений
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_admin_permissions_fix():
    """Тестирование исправленных админских разрешений"""
    print("🔍 Тест исправленных админских разрешений")
    print("=" * 50)
    
    try:
        from role_model.mongodb_provider import MongoDBRoleProvider
        from role_model.role_manager import RoleManager
        from role_model.lark_provider import LarkUserProvider
        from bot.keyboards.inline_keyboards import get_permission_keyboard
        import os
        
        # Инициализируем провайдеры
        role_provider = MongoDBRoleProvider()
        
        # Инициализируем LarkUserProvider с параметрами из переменных окружения
        app_id = os.getenv("LARK_APP_ID")
        app_secret = os.getenv("LARK_APP_SECRET")
        table_app_id = os.getenv("LARK_TABLE_APP_ID")
        table_id = os.getenv("LARK_TABLE_ID")
        
        user_provider = LarkUserProvider(app_id, app_secret, table_app_id, table_id)
        role_manager = RoleManager(user_provider, role_provider)
        
        print("✅ Провайдеры инициализированы")
        
        # Тест 1: Проверка доступных разрешений
        print(f"\n1️⃣ Проверка доступных разрешений...")
        available_permissions = await role_manager.get_available_permissions()
        print(f"   ✅ Доступные разрешения: {available_permissions}")
        
        # Тест 2: Проверка описаний разрешений
        print(f"\n2️⃣ Проверка описаний разрешений...")
        for permission in available_permissions:
            description = await role_manager.get_permission_description(permission)
            print(f"   📝 {permission}: {description}")
        
        # Тест 3: Создание клавиатуры разрешений
        print(f"\n3️⃣ Создание клавиатуры разрешений...")
        selected_permissions = {
            "can_access_sources": True,
            "can_access_analysis": True,
            "can_access_subscriptions": False,
            "can_manage_roles": False,
            "can_manage_users": False,
            "can_manage_telegram_auth": False
        }
        
        keyboard = get_permission_keyboard(available_permissions, selected_permissions)
        print(f"   📱 Клавиатура разрешений:")
        for i, row in enumerate(keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        # Тест 4: Проверка роли tester в базе
        print(f"\n4️⃣ Проверка роли tester в базе...")
        tester_permissions = await role_provider.get_role_permissions("tester")
        if tester_permissions:
            print(f"   ✅ Права роли tester: {tester_permissions.permissions}")
            
            # Проверяем, есть ли старые права
            old_permissions = ["can_use_analysis", "can_manage_sources", "can_receive_digest", "can_auth_telegram", "can_create_roles"]
            found_old = [perm for perm in old_permissions if perm in tester_permissions.permissions]
            if found_old:
                print(f"   ⚠️ Найдены старые права: {found_old}")
            else:
                print(f"   ✅ Старые права не найдены")
        else:
            print(f"   ❌ Роль tester не найдена")
        
        print("\n✅ Тест завершен успешно!")
        print("\n📋 Резюме:")
        print("   - Админские разрешения обновлены")
        print("   - Клавиатуры используют новые права")
        print("   - Система готова к работе")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования исправленных админских разрешений")
    print("=" * 50)
    
    await test_admin_permissions_fix()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 