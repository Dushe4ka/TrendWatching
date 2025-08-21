#!/usr/bin/env python3
"""
Тест исправленной системы ролей
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_role_system():
    """Тестирование исправленной системы ролей"""
    print("🔍 Тест исправленной системы ролей")
    print("=" * 50)
    
    try:
        from role_model.mongodb_provider import MongoDBRoleProvider
        from role_model.role_manager import RoleManager
        from role_model.lark_provider import LarkUserProvider
        
        # Инициализируем провайдеры
        role_provider = MongoDBRoleProvider()
        user_provider = LarkUserProvider()
        role_manager = RoleManager(user_provider, role_provider)
        
        print("✅ Провайдеры инициализированы")
        
        # Тест 1: Проверка существования роли 'tester'
        print(f"\n1️⃣ Проверка существования роли 'tester'...")
        exists = await role_provider.role_exists("tester")
        print(f"   ✅ role_exists('tester'): {exists}")
        
        # Тест 2: Получение разрешений роли 'tester'
        print(f"\n2️⃣ Получение разрешений роли 'tester'...")
        permissions = await role_provider.get_role_permissions("tester")
        if permissions:
            print(f"   ✅ Разрешения найдены: {permissions.permissions}")
        else:
            print(f"   ❌ Разрешения не найдены")
        
        # Тест 3: Получение всех ролей
        print(f"\n3️⃣ Получение всех ролей...")
        all_roles = await role_provider.get_all_roles()
        print(f"   ✅ Найдено {len(all_roles)} ролей:")
        for role in all_roles:
            print(f"      🏷️ {role.role_name}: {role.description}")
        
        # Тест 4: Проверка доступа пользователя @SHIFYuu
        print(f"\n4️⃣ Проверка доступа пользователя @SHIFYuu...")
        access_granted, error_message = await role_manager.check_user_access("SHIFYuu")
        print(f"   ✅ Доступ: {access_granted}")
        print(f"   📝 Сообщение: {error_message}")
        
        # Тест 5: Получение разрешений пользователя @SHIFYuu
        print(f"\n5️⃣ Получение разрешений пользователя @SHIFYuu...")
        user_permissions = await role_manager.get_user_permissions_by_username("SHIFYuu")
        print(f"   ✅ Разрешения: {user_permissions}")
        
        print("\n✅ Все тесты завершены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования исправленной системы ролей")
    print("=" * 50)
    
    await test_role_system()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 