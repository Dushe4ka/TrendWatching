#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы ролевой системы
"""

import asyncio
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_role_system_config
from role_model.lark_provider import LarkUserProvider, LarkRoleProvider
from role_model.role_manager import RoleManager


async def test_role_system():
    """Тестирование ролевой системы"""
    print("🧪 Начало тестирования ролевой системы")
    print("=" * 50)
    
    try:
        # Получаем конфигурацию
        role_config = get_role_system_config()["lark"]
        print(f"📋 Конфигурация получена: {role_config['app_id']}")
        
        # Создаем провайдеры
        user_provider = LarkUserProvider(
            app_id=role_config["app_id"],
            app_secret=role_config["app_secret"],
            table_app_id=role_config["table_app_id"],
            table_id=role_config["table_id"]
        )
        
        role_provider = LarkRoleProvider()
        
        # Создаем менеджер ролей
        role_manager = RoleManager(user_provider, role_provider)
        print("✅ Ролевой менеджер создан")
        
        # Тест 1: Получение всех пользователей
        print("\n📊 Тест 1: Получение пользователей")
        users = await role_manager.get_all_users()
        print(f"Найдено пользователей: {len(users)}")
        
        if users:
            print("Первые 3 пользователя:")
            for i, user in enumerate(users[:3]):
                print(f"  {i+1}. @{user.telegram_username} (ID: {user.user_id}, Роль: {user.role})")
        
        # Тест 2: Получение всех ролей
        print("\n📋 Тест 2: Получение ролей")
        roles = await role_manager.get_all_roles()
        print(f"Найдено ролей: {len(roles)}")
        
        for role in roles:
            permissions_count = sum(1 for perm, enabled in role.permissions.items() if enabled)
            print(f"  🔹 {role.role_name}: {permissions_count} разрешений")
        
        # Тест 3: Проверка разрешений для тестового пользователя
        print("\n🔑 Тест 3: Проверка разрешений")
        if users:
            test_user = users[0]
            test_user_id = test_user.user_id
            
            print(f"Тестируем пользователя: @{test_user.telegram_username} (ID: {test_user_id})")
            
            # Проверяем различные разрешения
            permissions_to_test = [
                "can_use_analysis",
                "can_manage_sources", 
                "can_receive_digest",
                "can_auth_telegram",
                "can_manage_users"
            ]
            
            for permission in permissions_to_test:
                has_permission = await role_manager.check_permission(test_user_id, permission)
                status = "✅" if has_permission else "❌"
                print(f"  {status} {permission}: {has_permission}")
        
        # Тест 4: Получение информации о пользователе
        print("\n👤 Тест 4: Информация о пользователе")
        if users:
            test_user = users[0]
            user_info = await role_manager.get_user_info(test_user.user_id)
            
            if user_info:
                print(f"  Пользователь: @{user_info.telegram_username}")
                print(f"  Роль: {user_info.role}")
                print(f"  Whitelisted: {user_info.is_whitelisted}")
                print(f"  Активен: {user_info.is_active}")
                print(f"  Компания: {user_info.company_id}")
        
        # Тест 5: Получение разрешений пользователя
        print("\n🔐 Тест 5: Разрешения пользователя")
        if users:
            test_user = users[0]
            permissions = await role_manager.get_user_permissions(test_user.user_id)
            
            if permissions:
                enabled_permissions = [perm for perm, enabled in permissions.items() if enabled]
                disabled_permissions = [perm for perm, enabled in permissions.items() if not enabled]
                
                print(f"  Разрешенные функции ({len(enabled_permissions)}):")
                for perm in enabled_permissions[:5]:  # Показываем первые 5
                    description = await role_manager.get_permission_description(perm)
                    print(f"    ✅ {description}")
                
                if len(enabled_permissions) > 5:
                    print(f"    ... и еще {len(enabled_permissions) - 5}")
                
                print(f"  Недоступные функции ({len(disabled_permissions)}):")
                for perm in disabled_permissions[:3]:  # Показываем первые 3
                    description = await role_manager.get_permission_description(perm)
                    print(f"    ❌ {description}")
                
                if len(disabled_permissions) > 3:
                    print(f"    ... и еще {len(disabled_permissions) - 3}")
        
        print("\n✅ Все тесты завершены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_specific_user(user_id: int):
    """Тестирование конкретного пользователя"""
    print(f"\n🧪 Тестирование пользователя с ID: {user_id}")
    print("=" * 30)
    
    try:
        # Получаем конфигурацию
        role_config = get_role_system_config()["lark"]
        
        # Создаем провайдеры
        user_provider = LarkUserProvider(
            app_id=role_config["app_id"],
            app_secret=role_config["app_secret"],
            table_app_id=role_config["table_app_id"],
            table_id=role_config["table_id"]
        )
        
        role_provider = LarkRoleProvider()
        
        # Создаем менеджер ролей
        role_manager = RoleManager(user_provider, role_provider)
        
        # Получаем информацию о пользователе
        user_info = await role_manager.get_user_info(user_id)
        
        if not user_info:
            print(f"❌ Пользователь с ID {user_id} не найден")
            return
        
        print(f"👤 Пользователь: @{user_info.telegram_username}")
        print(f"🔑 Роль: {user_info.role}")
        print(f"📊 Whitelisted: {user_info.is_whitelisted}")
        
        # Проверяем разрешения
        permissions = await role_manager.get_user_permissions(user_id)
        
        if permissions:
            enabled_permissions = [perm for perm, enabled in permissions.items() if enabled]
            print(f"\n✅ Разрешенные функции ({len(enabled_permissions)}):")
            for perm in enabled_permissions:
                description = await role_manager.get_permission_description(perm)
                print(f"  • {description}")
        
        # Тестируем конкретные разрешения
        test_permissions = [
            "can_use_analysis",
            "can_manage_sources",
            "can_receive_digest",
            "can_auth_telegram",
            "can_manage_users"
        ]
        
        print(f"\n🔍 Проверка разрешений:")
        for permission in test_permissions:
            has_permission = await role_manager.check_permission(user_id, permission)
            status = "✅" if has_permission else "❌"
            description = await role_manager.get_permission_description(permission)
            print(f"  {status} {permission}: {has_permission} ({description})")
        
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Тестирование ролевой системы")
    parser.add_argument("--user-id", type=int, help="ID пользователя для тестирования")
    
    args = parser.parse_args()
    
    if args.user_id:
        asyncio.run(test_specific_user(args.user_id))
    else:
        asyncio.run(test_role_system()) 