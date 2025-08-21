#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функционала администраторов
"""

import os
import sys
from dotenv import load_dotenv

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
load_dotenv()

def test_admin_functions():
    """Тестирует функции для работы с администраторами"""
    from bot.utils.misc import is_admin_from_env, is_admin, check_permission, get_user_role, get_user_info
    
    # Получаем список администраторов из переменных окружения
    admin_ids_str = os.getenv("ADMIN_ID", "")
    admin_ids = [admin_id.strip() for admin_id in admin_ids_str.split(",")] if admin_ids_str else []
    
    print("🔧 Тестирование функционала администраторов")
    print("=" * 50)
    
    print(f"📋 Администраторы из переменной ADMIN_ID: {admin_ids}")
    
    # Тестируем функции для каждого администратора
    for admin_id in admin_ids:
        if not admin_id:
            continue
            
        admin_id_int = int(admin_id)
        print(f"\n👤 Тестирование администратора ID: {admin_id}")
        
        # Тест функции is_admin_from_env
        is_admin_env = is_admin_from_env(admin_id_int)
        print(f"  ✅ is_admin_from_env: {is_admin_env}")
        
        # Тест функции get_user_role
        import asyncio
        role = asyncio.run(get_user_role(admin_id_int))
        print(f"  ✅ get_user_role: {role}")
        
        # Тест функции get_user_info
        user_info = asyncio.run(get_user_info(admin_id_int))
        if user_info:
            print(f"  ✅ get_user_info: user_id={user_info.user_id}, role={user_info.role}, whitelisted={user_info.is_whitelisted}")
        else:
            print(f"  ❌ get_user_info: None")
        
        # Тест функции check_permission
        has_permission = asyncio.run(check_permission(admin_id_int, "can_manage_users"))
        print(f"  ✅ check_permission('can_manage_users'): {has_permission}")
        
        has_analysis_permission = asyncio.run(check_permission(admin_id_int, "can_use_analysis"))
        print(f"  ✅ check_permission('can_use_analysis'): {has_analysis_permission}")
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено")

def test_non_admin_user():
    """Тестирует функции для обычного пользователя"""
    from bot.utils.misc import is_admin_from_env, check_permission, get_user_role, get_user_info
    
    # Тестируем с несуществующим пользователем
    test_user_id = 999999999
    
    print(f"\n👤 Тестирование обычного пользователя ID: {test_user_id}")
    
    # Тест функции is_admin_from_env
    is_admin_env = is_admin_from_env(test_user_id)
    print(f"  ✅ is_admin_from_env: {is_admin_env}")
    
    # Тест функции check_permission
    import asyncio
    has_permission = asyncio.run(check_permission(test_user_id, "can_manage_users"))
    print(f"  ✅ check_permission('can_manage_users'): {has_permission}")
    
    # Тест функции get_user_role
    role = asyncio.run(get_user_role(test_user_id))
    print(f"  ✅ get_user_role: {role}")
    
    # Тест функции get_user_info
    user_info = asyncio.run(get_user_info(test_user_id))
    if user_info:
        print(f"  ✅ get_user_info: user_id={user_info.user_id}, role={user_info.role}, whitelisted={user_info.is_whitelisted}")
    else:
        print(f"  ❌ get_user_info: None")

if __name__ == "__main__":
    print("🚀 Запуск тестирования функционала администраторов")
    print("=" * 50)
    
    # Проверяем наличие переменной ADMIN_ID
    admin_ids_str = os.getenv("ADMIN_ID", "")
    if not admin_ids_str:
        print("⚠️  ВНИМАНИЕ: Переменная ADMIN_ID не настроена!")
        print("   Добавьте в файл .env строку: ADMIN_ID=ваш_id_администратора")
        print("   Например: ADMIN_ID=123456789,987654321")
        print()
    
    test_admin_functions()
    test_non_admin_user()
    
    print("\n🎯 Рекомендации:")
    print("1. Убедитесь, что в файле .env настроена переменная ADMIN_ID")
    print("2. Добавьте туда ваш Telegram ID через запятую")
    print("3. Перезапустите бота после изменения .env файла")
    print("4. Администраторы будут иметь доступ ко всем функциям независимо от whitelist") 