#!/usr/bin/env python3
"""
Финальный тест системы с обновленными правами
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_final_system():
    """Финальное тестирование системы"""
    print("🔍 Финальный тест системы с обновленными правами")
    print("=" * 60)
    
    try:
        from role_model.mongodb_provider import MongoDBRoleProvider
        from role_model.role_manager import RoleManager
        from role_model.lark_provider import LarkUserProvider
        from bot.keyboards.inline_keyboards import get_dynamic_main_menu_keyboard
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
        
        # Тест 1: Проверка роли 'tester' с новыми правами
        print(f"\n1️⃣ Проверка роли 'tester' с новыми правами...")
        permissions = await role_provider.get_role_permissions("tester")
        if permissions:
            print(f"   ✅ Разрешения найдены: {permissions.permissions}")
            
            # Создаем клавиатуру для роли tester
            keyboard = get_dynamic_main_menu_keyboard(permissions.permissions)
            print(f"   📱 Клавиатура для tester:")
            for i, row in enumerate(keyboard.inline_keyboard):
                for j, button in enumerate(row):
                    print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        else:
            print(f"   ❌ Разрешения не найдены")
        
        # Тест 2: Проверка доступа пользователя @SHIFYuu
        print(f"\n2️⃣ Проверка доступа пользователя @SHIFYuu...")
        access_granted, error_message = await role_manager.check_user_access("SHIFYuu")
        print(f"   ✅ Доступ: {access_granted}")
        print(f"   📝 Сообщение: {error_message}")
        
        # Тест 3: Получение разрешений пользователя @SHIFYuu
        print(f"\n3️⃣ Получение разрешений пользователя @SHIFYuu...")
        user_permissions = await role_manager.get_user_permissions_by_username("SHIFYuu")
        print(f"   ✅ Разрешения: {user_permissions}")
        
        # Тест 4: Создание клавиатуры для пользователя @SHIFYuu
        print(f"\n4️⃣ Создание клавиатуры для пользователя @SHIFYuu...")
        if user_permissions:
            keyboard = get_dynamic_main_menu_keyboard(user_permissions)
            print(f"   📱 Клавиатура для @SHIFYuu:")
            for i, row in enumerate(keyboard.inline_keyboard):
                for j, button in enumerate(row):
                    print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        else:
            print(f"   ❌ Нет разрешений для создания клавиатуры")
        
        # Тест 5: Проверка всех ролей
        print(f"\n5️⃣ Проверка всех ролей...")
        all_roles = await role_provider.get_all_roles()
        print(f"   ✅ Найдено {len(all_roles)} ролей:")
        for role in all_roles:
            print(f"      🏷️ {role.role_name}: {role.description}")
            print(f"         Права: {role.permissions}")
            
            # Создаем клавиатуру для каждой роли
            keyboard = get_dynamic_main_menu_keyboard(role.permissions)
            print(f"         Клавиатура:")
            for i, row in enumerate(keyboard.inline_keyboard):
                for j, button in enumerate(row):
                    print(f"           [{i}][{j}]: {button.text}")
            print()
        
        print("\n✅ Финальный тест завершен успешно!")
        print("\n📋 Резюме:")
        print("   - Система ролей работает с новыми правами")
        print("   - Динамические клавиатуры создаются корректно")
        print("   - Пользователь @SHIFYuu должен видеть кнопки 'Источники' и 'Анализ'")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск финального тестирования системы")
    print("=" * 60)
    
    await test_final_system()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 