#!/usr/bin/env python3
"""
Тестовый скрипт для проверки инициализации ролевой системы
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
load_dotenv()

async def test_role_system_initialization():
    """Тестирует инициализацию ролевой системы"""
    print("🔧 Тестирование инициализации ролевой системы")
    print("=" * 50)
    
    try:
        # Тест 1: Проверяем конфигурацию
        print("1. Проверка конфигурации...")
        from config import get_role_system_config
        role_config = get_role_system_config()
        print(f"   ✅ Конфигурация получена: {role_config}")
        
        # Тест 2: Проверяем импорт провайдеров
        print("\n2. Проверка импорта провайдеров...")
        from role_model.lark_provider import LarkUserProvider
        from role_model.mongodb_provider import MongoDBRoleProvider
        from role_model.role_manager import RoleManager
        print("   ✅ Все провайдеры импортированы успешно")
        
        # Тест 3: Создание провайдеров
        print("\n3. Создание провайдеров...")
        lark_config = role_config["lark"]
        
        user_provider = LarkUserProvider(
            app_id=lark_config["app_id"],
            app_secret=lark_config["app_secret"],
            table_app_id=lark_config["table_app_id"],
            table_id=lark_config["table_id"]
        )
        print("   ✅ LarkUserProvider создан")
        
        role_provider = MongoDBRoleProvider()
        print("   ✅ MongoDBRoleProvider создан")
        
        # Тест 4: Создание менеджера ролей
        print("\n4. Создание менеджера ролей...")
        role_manager = RoleManager(user_provider, role_provider)
        print("   ✅ RoleManager создан")
        
        # Тест 5: Проверка методов менеджера
        print("\n5. Проверка методов менеджера...")
        
        # Проверяем получение всех ролей
        try:
            roles = await role_manager.get_all_roles()
            print(f"   ✅ get_all_roles(): получено {len(roles)} ролей")
        except Exception as e:
            print(f"   ❌ get_all_roles(): ошибка - {str(e)}")
        
        # Проверяем получение доступных разрешений
        try:
            permissions = await role_manager.get_available_permissions()
            print(f"   ✅ get_available_permissions(): получено {len(permissions)} разрешений")
        except Exception as e:
            print(f"   ❌ get_available_permissions(): ошибка - {str(e)}")
        
        # Проверяем проверку существования роли
        try:
            exists = await role_manager.role_exists("test_role")
            print(f"   ✅ role_exists(): {exists}")
        except Exception as e:
            print(f"   ❌ role_exists(): ошибка - {str(e)}")
        
        print("\n" + "=" * 50)
        print("✅ Тестирование завершено успешно")
        return role_manager
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {str(e)}")
        print(f"   Тип ошибки: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None

async def test_main_role_manager():
    """Тестирует функцию get_role_manager из main.py"""
    print("\n🔧 Тестирование get_role_manager из main.py")
    print("=" * 50)
    
    try:
        # Импортируем функцию инициализации
        from main import initialize_role_system, get_role_manager
        
        # Инициализируем систему
        print("1. Инициализация ролевой системы...")
        role_manager = await initialize_role_system()
        
        if role_manager:
            print("   ✅ Ролевая система инициализирована")
        else:
            print("   ❌ Ролевая система не инициализирована")
            return None
        
        # Проверяем функцию get_role_manager
        print("\n2. Проверка get_role_manager...")
        retrieved_manager = get_role_manager()
        
        if retrieved_manager:
            print("   ✅ get_role_manager() возвращает менеджер")
        else:
            print("   ❌ get_role_manager() возвращает None")
            return None
        
        # Проверяем методы
        print("\n3. Проверка методов менеджера...")
        
        try:
            roles = await retrieved_manager.get_all_roles()
            print(f"   ✅ get_all_roles(): {len(roles)} ролей")
        except Exception as e:
            print(f"   ❌ get_all_roles(): {str(e)}")
        
        try:
            permissions = await retrieved_manager.get_available_permissions()
            print(f"   ✅ get_available_permissions(): {len(permissions)} разрешений")
        except Exception as e:
            print(f"   ❌ get_available_permissions(): {str(e)}")
        
        print("\n" + "=" * 50)
        print("✅ Тестирование main.py завершено")
        return retrieved_manager
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании main.py: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 Запуск тестирования ролевой системы")
    print("=" * 50)
    
    # Проверяем переменные окружения
    print("📋 Проверка переменных окружения:")
    required_vars = [
        "LARK_APP_ID", "LARK_APP_SECRET", "LARK_TABLE_APP_ID", "LARK_TABLE_ID",
        "MONGODB_URI", "MONGODB_DB"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value[:10]}..." if len(value) > 10 else f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: не установлена")
    
    print()
    
    # Запускаем тесты
    asyncio.run(test_role_system_initialization())
    asyncio.run(test_main_role_manager())
    
    print("\n🎯 Рекомендации:")
    print("1. Убедитесь, что все переменные окружения установлены")
    print("2. Проверьте подключение к MongoDB")
    print("3. Проверьте доступ к Lark API")
    print("4. Перезапустите бота после исправления ошибок") 