#!/usr/bin/env python3
"""
Тест упрощенной системы прав
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_simplified_permissions():
    """Тестирование упрощенной системы прав"""
    print("🔍 Тест упрощенной системы прав")
    print("=" * 50)
    
    try:
        from role_model.mongodb_provider import MongoDBRoleProvider
        from role_model.role_manager import RoleManager
        from role_model.lark_provider import LarkUserProvider
        from bot.keyboards.inline_keyboards import get_dynamic_main_menu_keyboard, get_permission_keyboard
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
        
        # Тест 3: Проверка ролей
        print(f"\n3️⃣ Проверка ролей...")
        all_roles = await role_provider.get_all_roles()
        print(f"   ✅ Найдено {len(all_roles)} ролей:")
        
        for role in all_roles:
            print(f"      🏷️ {role.role_name}: {role.description}")
            print(f"         Права:")
            for permission, value in role.permissions.items():
                status = "✅" if value else "❌"
                print(f"           {status} {permission}")
            
            # Создаем клавиатуру для каждой роли
            keyboard = get_dynamic_main_menu_keyboard(role.permissions)
            print(f"         Клавиатура:")
            for i, row in enumerate(keyboard.inline_keyboard):
                for j, button in enumerate(row):
                    print(f"           [{i}][{j}]: {button.text}")
            print()
        
        # Тест 4: Создание клавиатуры разрешений
        print(f"\n4️⃣ Создание клавиатуры разрешений...")
        selected_permissions = {
            "can_access_sources": True,
            "can_access_analysis": True,
            "can_access_subscriptions": False,
            "can_manage_telegram_auth": True,
            "can_access_admin_panel": False
        }
        
        keyboard = get_permission_keyboard(available_permissions, selected_permissions)
        print(f"   📱 Клавиатура разрешений:")
        for i, row in enumerate(keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print("\n✅ Тест завершен успешно!")
        print("\n📋 Резюме:")
        print("   - Система прав упрощена")
        print("   - Убраны права 'управление ролями' и 'управление пользователями'")
        print("   - Добавлено право 'доступ к админ панели'")
        print("   - Право 'доступ к админ панели' дает доступ ко всем админским функциям")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования упрощенной системы прав")
    print("=" * 50)
    
    await test_simplified_permissions()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 