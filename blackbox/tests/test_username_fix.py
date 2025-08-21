#!/usr/bin/env python3
"""
Тест для проверки исправленной логики с username
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_username_logic():
    """Тестирование логики с username"""
    print("🔍 Тестирование исправленной логики с username")
    print("=" * 60)
    
    try:
        from bot.utils.misc import check_user_access, check_permission
        from role_model.lark_provider import LarkUserProvider
        from config import get_role_system_config
        
        # Получаем конфигурацию
        role_config = get_role_system_config()
        lark_config = role_config["lark"]
        
        # Создаем провайдер
        user_provider = LarkUserProvider(
            app_id=lark_config["app_id"],
            app_secret=lark_config["app_secret"],
            table_app_id=lark_config["table_app_id"],
            table_id=lark_config["table_id"]
        )
        
        print("✅ LarkUserProvider создан")
        print()
        
        # Тестируем с разными пользователями
        test_cases = [
            (5032415442, "SHIFYuu"),  # Должен работать
            (5032415442, "Lavkaaa_helper"),  # Статус "Уволен"
            (123456789, "test_user"),  # Не существует
        ]
        
        for user_id, username in test_cases:
            print(f"🔍 Тестирование: ID {user_id}, username @{username}")
            print("-" * 50)
            
            # Тест 1: check_user_access
            print(f"1️⃣ Тест check_user_access...")
            access_granted, message, role = await check_user_access(user_id, username)
            print(f"   Результат: {'✅ Доступ разрешен' if access_granted else '❌ Доступ запрещен'}")
            print(f"   Сообщение: {message}")
            print(f"   Роль: {role}")
            
            # Тест 2: check_permission
            print(f"2️⃣ Тест check_permission...")
            has_permission = await check_permission(user_id, "can_use_analysis", username)
            print(f"   Результат: {'✅ Разрешение есть' if has_permission else '❌ Разрешения нет'}")
            
            print()
        
        # Тест 3: Проверка через user_provider напрямую
        print(f"3️⃣ Тест через user_provider напрямую")
        print("-" * 50)
        
        for username in ["SHIFYuu", "Lavkaaa_helper", "test_user"]:
            print(f"🔍 Проверка @{username}...")
            
            # Ищем пользователя
            user_doc = await user_provider.get_user_by_username_from_lark(username)
            
            if user_doc:
                print(f"✅ Пользователь найден:")
                print(f"   - Username: {user_doc.get('username', 'N/A')}")
                print(f"   - Имя: {user_doc.get('employee_name', 'N/A')}")
                print(f"   - Роль: {user_doc.get('role', 'N/A')}")
                print(f"   - Статус: {user_doc.get('employee_status', 'N/A')}")
                
                # Проверяем доступ
                access_granted, error_message = await user_provider.check_user_access(username)
                print(f"   - Доступ: {'✅ Разрешен' if access_granted else '❌ Запрещен'}")
                if not access_granted:
                    print(f"   - Причина: {error_message}")
            else:
                print(f"❌ Пользователь НЕ найден")
            
            print()
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования исправленной логики")
    print("=" * 60)
    
    await test_username_logic()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 