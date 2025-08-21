#!/usr/bin/env python3
"""
Тест для проверки исправлений
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_mongodb_provider():
    """Тестирование MongoDBRoleProvider"""
    print("🔧 Тестирование MongoDBRoleProvider")
    print("=" * 50)
    
    try:
        # Тест 1: Импорт MongoDBRoleProvider
        print("1. Импорт MongoDBRoleProvider...")
        from role_model.mongodb_provider import MongoDBRoleProvider
        print("   ✅ MongoDBRoleProvider импортирован")
        
        # Тест 2: Создание экземпляра
        print("\n2. Создание экземпляра...")
        provider = MongoDBRoleProvider()
        print("   ✅ Экземпляр создан")
        
        # Тест 3: Проверка метода ensure_default_roles
        print("\n3. Проверка метода ensure_default_roles...")
        await provider.ensure_default_roles()
        print("   ✅ ensure_default_roles выполнен")
        
        # Тест 4: Проверка метода role_exists
        print("\n4. Проверка метода role_exists...")
        exists = await provider.role_exists("admin")
        print(f"   ✅ role_exists('admin'): {exists}")
        
        # Тест 5: Получение всех ролей
        print("\n5. Получение всех ролей...")
        roles = await provider.get_all_roles()
        print(f"   ✅ Найдено ролей: {len(roles)}")
        for role in roles:
            print(f"      - {role.role_name}: {role.description}")
        
        print("\n✅ Тестирование MongoDBRoleProvider завершено успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании MongoDBRoleProvider: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_imports():
    """Тестирование импортов"""
    print("\n📦 Тестирование импортов")
    print("=" * 50)
    
    try:
        # Тест 1: Импорт admin_handlers
        print("1. Импорт admin_handlers...")
        from bot.handlers.admin_handlers import cmd_users
        print("   ✅ cmd_users импортирован")
        
        # Тест 2: Импорт misc
        print("\n2. Импорт misc...")
        from bot.utils.misc import is_admin, check_permission, get_user_info
        print("   ✅ Функции из misc импортированы")
        
        # Тест 3: Импорт inline_keyboards
        print("\n3. Импорт inline_keyboards...")
        from bot.keyboards.inline_keyboards import get_admin_keyboard
        print("   ✅ get_admin_keyboard импортирован")
        
        print("\n✅ Тестирование импортов завершено успешно!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании импортов: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_role_system():
    """Тестирование ролевой системы"""
    print("\n🔐 Тестирование ролевой системы")
    print("=" * 50)
    
    try:
        # Тест 1: Инициализация ролевой системы
        print("1. Инициализация ролевой системы...")
        from main import initialize_role_system
        role_manager = await initialize_role_system()
        
        if role_manager:
            print("   ✅ Ролевая система инициализирована")
            
            # Тест 2: Проверка доступа
            print("\n2. Проверка доступа...")
            test_username = "alexdru"  # Замените на ваш username
            access_granted, error_message = await role_manager.check_user_access(test_username)
            print(f"   🔍 Доступ для @{test_username}: {'✅ Разрешен' if access_granted else '❌ Запрещен'}")
            if not access_granted:
                print(f"   📝 Причина: {error_message}")
        else:
            print("   ❌ Ролевая система не инициализирована")
        
        print("\n✅ Тестирование ролевой системы завершено!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании ролевой системы: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестов исправлений")
    print("=" * 80)
    
    await test_mongodb_provider()
    await test_imports()
    await test_role_system()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 