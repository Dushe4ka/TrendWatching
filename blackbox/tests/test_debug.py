#!/usr/bin/env python3
"""
Тест для проверки дебага ролевой системы
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

async def test_debug_system():
    """Тестирование дебага ролевой системы"""
    print("🔍 Тестирование дебага ролевой системы")
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
        
        # Тест 2: Проверка доступа для тестового пользователя
        print("\n2. Проверка доступа для тестового пользователя...")
        test_username = "alexdru"  # Замените на ваш username
        
        print(f"   🔍 Проверяем доступ для @{test_username}...")
        access_granted, error_message = await role_manager.check_user_access(test_username)
        
        if access_granted:
            print(f"   ✅ Доступ разрешен для @{test_username}")
        else:
            print(f"   ❌ Доступ НЕ разрешен для @{test_username}: {error_message}")
        
        # Тест 3: Получение информации о пользователе
        print("\n3. Получение информации о пользователе...")
        try:
            # Создаем фиктивный user_id для теста
            test_user_id = 123456789
            
            print(f"   🔍 Получаем информацию для user_id: {test_user_id}")
            user_info = await role_manager.get_user_info(test_user_id)
            
            if user_info:
                print(f"   ✅ Информация о пользователе найдена:")
                print(f"      ID: {user_info.user_id}")
                print(f"      Username: @{user_info.telegram_username}")
                print(f"      Роль: {user_info.role}")
            else:
                print(f"   ❌ Информация о пользователе не найдена")
        except Exception as e:
            print(f"   ❌ Ошибка при получении информации о пользователе: {e}")
        
        # Тест 4: Проверка разрешений
        print("\n4. Проверка разрешений...")
        try:
            test_user_id = 123456789
            test_permission = "can_use_analysis"
            
            print(f"   🔍 Проверяем разрешение '{test_permission}' для user_id: {test_user_id}")
            has_permission = await role_manager.check_permission(test_user_id, test_permission)
            
            if has_permission:
                print(f"   ✅ У пользователя ЕСТЬ разрешение '{test_permission}'")
            else:
                print(f"   ❌ У пользователя НЕТ разрешения '{test_permission}'")
        except Exception as e:
            print(f"   ❌ Ошибка при проверке разрешений: {e}")
        
        print("\n✅ Все тесты дебага завершены!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_collection_content():
    """Тестирование содержимого коллекции users_lark"""
    print("\n📊 Тестирование содержимого коллекции users_lark")
    print("=" * 60)
    
    try:
        from database import db
        
        # Проверяем количество пользователей
        count = db.users_lark.count_documents({})
        print(f"1. Всего пользователей в коллекции users_lark: {count}")
        
        if count > 0:
            # Показываем всех пользователей
            print("\n2. Список пользователей:")
            users = list(db.users_lark.find({}))
            
            for i, user in enumerate(users, 1):
                print(f"   {i}. Username: @{user.get('username', 'N/A')}")
                print(f"      Имя: {user.get('employee_name', 'N/A')}")
                print(f"      Роль: {user.get('role', 'N/A')}")
                print(f"      Статус: {user.get('status', 'N/A')}")
                print(f"      Статус сотрудника: {user.get('employee_status', 'N/A')}")
                print(f"      Синхронизировано: {user.get('synced_at', 'N/A')}")
                print()
        else:
            print("   ❌ Коллекция users_lark пуста")
        
        # Проверяем коллекцию roles
        print("3. Проверка коллекции roles:")
        roles_count = db.roles.count_documents({})
        print(f"   Всего ролей: {roles_count}")
        
        if roles_count > 0:
            roles = list(db.roles.find({}))
            for i, role in enumerate(roles, 1):
                print(f"   {i}. Роль: {role.get('role_name', 'N/A')}")
                print(f"      Описание: {role.get('description', 'N/A')}")
                permissions = role.get('permissions', {})
                enabled_permissions = sum(1 for perm, enabled in permissions.items() if enabled)
                print(f"      Разрешений: {len(permissions)}, включено: {enabled_permissions}")
                print()
        
        print("✅ Проверка коллекций завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка при проверке коллекций: {e}")


async def main():
    """Основная функция"""
    print(f"🚀 Запуск тестов дебага ролевой системы - {datetime.now()}")
    print("=" * 80)
    
    await test_debug_system()
    await test_collection_content()
    
    print(f"\n🏁 Тестирование завершено - {datetime.now()}")


if __name__ == "__main__":
    asyncio.run(main()) 