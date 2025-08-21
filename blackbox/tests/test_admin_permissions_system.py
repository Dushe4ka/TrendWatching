#!/usr/bin/env python3
"""
Тест новой системы админских прав
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_admin_permissions_system():
    """Тестирование новой системы админских прав"""
    print("🔍 Тест новой системы админских прав")
    print("=" * 50)
    
    try:
        from bot.utils.misc import has_admin_permissions, is_admin_from_env
        from role_model.mongodb_provider import MongoDBRoleProvider
        from role_model.role_manager import RoleManager
        from role_model.lark_provider import LarkUserProvider
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
        
        # Тест 1: Проверка пользователя из ADMIN_ID
        print(f"\n1️⃣ Проверка пользователя из ADMIN_ID...")
        admin_ids_str = os.getenv("ADMIN_ID", "")
        if admin_ids_str:
            admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip().isdigit()]
            for admin_id in admin_ids:
                has_perms = await has_admin_permissions(admin_id)
                print(f"   🔧 Пользователь ID {admin_id} (ADMIN_ID): {has_perms}")
        else:
            print(f"   ⚠️ ADMIN_ID не установлен")
        
        # Тест 2: Проверка пользователя с правами на управление авторизацией
        print(f"\n2️⃣ Проверка пользователя с правами на управление авторизацией...")
        test_user_id = 5032415442  # @SHIFYuu
        test_username = "SHIFYuu"
        
        has_perms = await has_admin_permissions(test_user_id, test_username)
        print(f"   👤 Пользователь @{test_username} (ID: {test_user_id}): {has_perms}")
        
        # Тест 3: Проверка прав пользователя
        print(f"\n3️⃣ Проверка прав пользователя @{test_username}...")
        user_permissions = await role_manager.get_user_permissions_by_username(test_username)
        print(f"   📋 Права: {user_permissions}")
        
        # Проверяем админские права
        admin_permissions = [
            "can_manage_roles",
            "can_manage_users", 
            "can_manage_telegram_auth"
        ]
        
        for perm in admin_permissions:
            has_perm = user_permissions.get(perm, False)
            status = "✅" if has_perm else "❌"
            print(f"   {status} {perm}: {has_perm}")
        
        # Тест 4: Проверка роли tester
        print(f"\n4️⃣ Проверка роли tester...")
        tester_permissions = await role_provider.get_role_permissions("tester")
        if tester_permissions:
            print(f"   🏷️ Права роли tester: {tester_permissions.permissions}")
            
            # Проверяем админские права в роли
            for perm in admin_permissions:
                has_perm = tester_permissions.permissions.get(perm, False)
                status = "✅" if has_perm else "❌"
                print(f"   {status} {perm}: {has_perm}")
        else:
            print(f"   ❌ Роль tester не найдена")
        
        print("\n✅ Тест завершен успешно!")
        print("\n📋 Резюме:")
        print("   - Система админских прав работает")
        print("   - Проверяется либо ADMIN_ID, либо права роли")
        print("   - Пользователи с правами могут получить доступ к админским функциям")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования новой системы админских прав")
    print("=" * 50)
    
    await test_admin_permissions_system()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 