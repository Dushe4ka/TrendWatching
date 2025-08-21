#!/usr/bin/env python3
"""
Тестовый скрипт для проверки MongoDB ролевой системы
"""

import asyncio
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from role_model.mongodb_provider import MongoDBRoleProvider


async def test_mongodb_roles():
    """Тестирование MongoDB ролевой системы"""
    print("🧪 Начало тестирования MongoDB ролевой системы")
    print("=" * 60)
    
    try:
        # Создаем провайдер
        role_provider = MongoDBRoleProvider()
        print("✅ MongoDB провайдер создан")
        
        # Тест 1: Получение всех ролей
        print("\n📋 Тест 1: Получение всех ролей")
        roles = await role_provider.get_all_roles()
        print(f"Найдено ролей: {len(roles)}")
        
        for role in roles:
            permissions_count = sum(1 for perm, enabled in role.permissions.items() if enabled)
            print(f"  🔹 {role.role_name}: {permissions_count} разрешений")
            print(f"     📝 {role.description}")
        
        # Тест 2: Получение конкретной роли
        print("\n🔍 Тест 2: Получение конкретной роли")
        admin_role = await role_provider.get_role_permissions("admin")
        if admin_role:
            print(f"✅ Роль 'admin' найдена")
            print(f"   Разрешений: {sum(admin_role.permissions.values())}")
            print(f"   Описание: {admin_role.description}")
        else:
            print("❌ Роль 'admin' не найдена")
        
        # Тест 3: Проверка существования роли
        print("\n🔍 Тест 3: Проверка существования ролей")
        test_roles = ["admin", "manager", "nonexistent"]
        for role_name in test_roles:
            exists = await role_provider.role_exists(role_name)
            status = "✅" if exists else "❌"
            print(f"  {status} {role_name}: {exists}")
        
        # Тест 4: Получение информации о роли
        print("\n📊 Тест 4: Получение информации о роли")
        role_info = await role_provider.get_role_info("manager")
        if role_info:
            print(f"✅ Информация о роли 'manager':")
            print(f"   Название: {role_info['role_name']}")
            print(f"   Описание: {role_info['description']}")
            print(f"   Создана: {role_info['created_at']}")
            print(f"   Обновлена: {role_info['updated_at']}")
            print(f"   Разрешений: {len(role_info['permissions'])}")
        else:
            print("❌ Информация о роли 'manager' не найдена")
        
        # Тест 5: Получение доступных разрешений
        print("\n🔑 Тест 5: Доступные разрешения")
        permissions = await role_provider.get_available_permissions()
        print(f"Доступно разрешений: {len(permissions)}")
        for perm in permissions:
            description = await role_provider.get_permission_description(perm)
            print(f"  • {perm}: {description}")
        
        print("\n✅ Все тесты MongoDB ролевой системы завершены успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_role_operations():
    """Тестирование операций с ролями"""
    print("\n🧪 Тестирование операций с ролями")
    print("=" * 50)
    
    try:
        role_provider = MongoDBRoleProvider()
        
        # Тест создания роли
        print("\n➕ Тест создания роли")
        test_permissions = {
            "can_use_analysis": True,
            "can_receive_digest": True,
            "can_view_statistics": True
        }
        
        success = await role_provider.create_role(
            "test_role", 
            test_permissions, 
            "Тестовая роль для проверки"
        )
        
        if success:
            print("✅ Тестовая роль создана")
            
            # Проверяем, что роль создана
            role = await role_provider.get_role_permissions("test_role")
            if role:
                print(f"✅ Роль найдена: {role.role_name}")
                print(f"   Разрешений: {sum(role.permissions.values())}")
            
            # Тест обновления роли
            print("\n🔧 Тест обновления роли")
            updated_permissions = {
                "can_use_analysis": True,
                "can_receive_digest": True,
                "can_view_statistics": True,
                "can_export_data": True
            }
            
            update_success = await role_provider.update_role(
                "test_role",
                updated_permissions,
                "Обновленная тестовая роль"
            )
            
            if update_success:
                print("✅ Роль обновлена")
                
                # Проверяем обновление
                updated_role = await role_provider.get_role_permissions("test_role")
                if updated_role:
                    print(f"✅ Обновленная роль: {updated_role.description}")
                    print(f"   Разрешений: {sum(updated_role.permissions.values())}")
            
            # Тест удаления роли
            print("\n🗑️ Тест удаления роли")
            delete_success = await role_provider.delete_role("test_role")
            
            if delete_success:
                print("✅ Роль удалена")
                
                # Проверяем удаление
                deleted_role = await role_provider.get_role_permissions("test_role")
                if not deleted_role:
                    print("✅ Роль успешно удалена из базы")
                else:
                    print("❌ Роль все еще существует")
            else:
                print("❌ Ошибка при удалении роли")
        else:
            print("❌ Ошибка при создании тестовой роли")
        
        print("\n✅ Тестирование операций завершено!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании операций: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mongodb_roles())
    asyncio.run(test_role_operations()) 