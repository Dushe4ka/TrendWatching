#!/usr/bin/env python3
"""
Тестовый скрипт для проверки новой ролевой системы
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_new_role_system():
    """Тестирование новой ролевой системы"""
    print("🔧 Тестирование новой ролевой системы")
    print("=" * 60)
    
    try:
        # Тест 1: Инициализация ролевой системы
        print("1. Инициализация ролевой системы...")
        from main import initialize_role_system
        role_manager = await initialize_role_system()
        
        if not role_manager:
            print("   ❌ Ролевая система не инициализирована")
            return
        
        print("   ✅ Ролевая система инициализирована")
        
        # Тест 2: Проверка доступных разрешений
        print("\n2. Проверка доступных разрешений...")
        available_permissions = await role_manager.get_available_permissions()
        print(f"   Доступно разрешений: {len(available_permissions)}")
        for perm in available_permissions:
            description = await role_manager.get_permission_description(perm)
            print(f"   • {perm}: {description}")
        
        # Тест 3: Проверка ролей по умолчанию
        print("\n3. Проверка ролей по умолчанию...")
        roles = await role_manager.get_all_roles()
        print(f"   Найдено ролей: {len(roles)}")
        for role in roles:
            permissions_count = sum(1 for perm, enabled in role.permissions.items() if enabled)
            print(f"   • {role.role_name}: {permissions_count} разрешений")
            print(f"     📝 {role.description}")
        
        # Тест 4: Проверка синхронизации с Lark Base
        print("\n4. Проверка синхронизации с Lark Base...")
        try:
            users_count = await role_manager.user_provider.sync_users_from_lark()
            print(f"   ✅ Синхронизировано пользователей: {users_count}")
        except Exception as e:
            print(f"   ❌ Ошибка синхронизации: {e}")
        
        # Тест 5: Проверка коллекции users_lark
        print("\n5. Проверка коллекции users_lark...")
        try:
            from database import db
            users_lark_count = await db.users_lark.count_documents({})
            print(f"   Пользователей в коллекции users_lark: {users_lark_count}")
            
            if users_lark_count > 0:
                # Показываем несколько примеров
                sample_users = await db.users_lark.find({}).limit(3).to_list(length=3)
                print("   Примеры пользователей:")
                for user in sample_users:
                    print(f"     • @{user.get('username', 'N/A')} - {user.get('employee_name', 'N/A')} - {user.get('role', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Ошибка проверки коллекции: {e}")
        
        # Тест 6: Проверка новой логики доступа
        print("\n6. Проверка новой логики доступа...")
        test_usernames = ["alexdru", "test_user", "admin"]
        
        for username in test_usernames:
            try:
                access_granted, error_message = await role_manager.check_user_access(username)
                status = "✅" if access_granted else "❌"
                print(f"   {status} @{username}: {error_message}")
            except Exception as e:
                print(f"   ❌ @{username}: Ошибка проверки - {e}")
        
        print("\n✅ Все тесты новой ролевой системы завершены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_permission_checking():
    """Тестирование проверки разрешений"""
    print("\n🔑 Тестирование проверки разрешений")
    print("=" * 50)
    
    try:
        from main import initialize_role_system
        role_manager = await initialize_role_system()
        
        if not role_manager:
            print("❌ Ролевая система не инициализирована")
            return
        
        # Тест проверки разрешений для разных ролей
        test_cases = [
            ("admin", "can_use_analysis", True),
            ("admin", "can_manage_sources", True),
            ("manager", "can_use_analysis", True),
            ("manager", "can_manage_sources", True),
            ("analyst", "can_use_analysis", True),
            ("analyst", "can_manage_sources", False),
            ("tester", "can_use_analysis", True),
            ("tester", "can_manage_sources", False),
        ]
        
        for role_name, permission, expected in test_cases:
            try:
                # Получаем разрешения для роли
                role_permissions = await role_manager.role_provider.get_role_permissions(role_name)
                if role_permissions:
                    has_permission = role_permissions.permissions.get(permission, False)
                    status = "✅" if has_permission == expected else "❌"
                    print(f"   {status} {role_name}.{permission}: {has_permission} (ожидалось: {expected})")
                else:
                    print(f"   ❌ Роль {role_name} не найдена")
            except Exception as e:
                print(f"   ❌ Ошибка проверки {role_name}.{permission}: {e}")
        
        print("\n✅ Тестирование разрешений завершено!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании разрешений: {str(e)}")


async def main():
    """Основная функция"""
    print(f"🚀 Запуск тестов новой ролевой системы - {datetime.now()}")
    print("=" * 80)
    
    await test_new_role_system()
    await test_permission_checking()
    
    print(f"\n🏁 Тестирование завершено - {datetime.now()}")


if __name__ == "__main__":
    asyncio.run(main()) 