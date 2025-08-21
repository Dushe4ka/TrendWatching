#!/usr/bin/env python3
"""
Тест для проверки обработки username из Telegram
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_username_processing():
    """Тестирование обработки username"""
    print("🔍 Тестирование обработки username из Telegram")
    print("=" * 80)
    
    # Симулируем разные варианты username, которые могут прийти из Telegram
    test_usernames = [
        "SHIFYuu",           # Обычный username
        "@SHIFYuu",          # С символом @
        "shifyuu",           # В нижнем регистре
        "@shifyuu",          # С символом @ в нижнем регистре
        "SHIFYuu ",          # С пробелом в конце
        " SHIFYuu",          # С пробелом в начале
        "@SHIFYuu ",         # С символом @ и пробелом
        "Lavkaaa_helper",    # Другой пользователь
        "@Lavkaaa_helper",   # С символом @
    ]
    
    try:
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
        
        for username in test_usernames:
            print(f"🔍 Тестирование username: '{username}'")
            print("-" * 50)
            
            # Показываем, как username приходит из Telegram
            print(f"📱 Username из Telegram: '{username}'")
            
            # Показываем, как он обрабатывается в check_user_access
            clean_username = username.lstrip('@')
            print(f"🧹 Очищенный username: '{clean_username}'")
            
            # Ищем пользователя
            user_doc = await user_provider.get_user_by_username_from_lark(clean_username)
            
            if user_doc:
                print(f"✅ Пользователь найден:")
                print(f"   - Username в БД: '{user_doc.get('username', 'N/A')}'")
                print(f"   - Имя: {user_doc.get('employee_name', 'N/A')}")
                print(f"   - Роль: {user_doc.get('role', 'N/A')}")
                print(f"   - Статус сотрудника: {user_doc.get('employee_status', 'N/A')}")
                
                # Проверяем доступ
                access_granted, error_message = await user_provider.check_user_access(username)
                print(f"🔐 Доступ: {'✅ Разрешен' if access_granted else '❌ Запрещен'}")
                if not access_granted:
                    print(f"   Причина: {error_message}")
            else:
                print(f"❌ Пользователь НЕ найден")
            
            print()
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


async def test_telegram_message_simulation():
    """Симуляция сообщения из Telegram"""
    print("\n📱 Симуляция сообщения из Telegram")
    print("=" * 80)
    
    # Симулируем объект Message из aiogram
    class MockMessage:
        def __init__(self, user_id: int, username: str):
            self.from_user = MockUser(user_id, username)
    
    class MockUser:
        def __init__(self, user_id: int, username: str):
            self.id = user_id
            self.username = username
    
    # Тестируем с разными пользователями
    test_cases = [
        (1395854084, "SHIFYuu"),
        (5032415442, "Lavkaaa_helper"),
        (123456789, "test_user"),
    ]
    
    for user_id, username in test_cases:
        print(f"\n🔍 Симуляция пользователя ID: {user_id}, username: {username}")
        print("-" * 50)
        
        # Создаем мок-сообщение
        message = MockMessage(user_id, username)
        
        print(f"📱 Данные из Telegram:")
        print(f"   - User ID: {message.from_user.id}")
        print(f"   - Username: '{message.from_user.username}'")
        
        if not message.from_user.username:
            print(f"❌ У пользователя нет username")
            continue
        
        # Показываем, как username будет обработан
        clean_username = message.from_user.username.lstrip('@')
        print(f"🧹 Обработанный username: '{clean_username}'")
        
        # Тестируем поиск в системе
        try:
            from role_model.lark_provider import LarkUserProvider
            from config import get_role_system_config
            
            role_config = get_role_system_config()
            lark_config = role_config["lark"]
            
            user_provider = LarkUserProvider(
                app_id=lark_config["app_id"],
                app_secret=lark_config["app_secret"],
                table_app_id=lark_config["table_app_id"],
                table_id=lark_config["table_id"]
            )
            
            user_doc = await user_provider.get_user_by_username_from_lark(clean_username)
            
            if user_doc:
                print(f"✅ Пользователь найден в системе:")
                print(f"   - Username в БД: '{user_doc.get('username', 'N/A')}'")
                print(f"   - Статус: {user_doc.get('employee_status', 'N/A')}")
                print(f"   - Роль: {user_doc.get('role', 'N/A')}")
                
                # Проверяем доступ
                access_granted, error_message = await user_provider.check_user_access(message.from_user.username)
                print(f"🔐 Доступ: {'✅ Разрешен' if access_granted else '❌ Запрещен'}")
                if not access_granted:
                    print(f"   Причина: {error_message}")
            else:
                print(f"❌ Пользователь НЕ найден в системе")
                print(f"   Возможные причины:")
                print(f"   - Username '{clean_username}' отсутствует в Lark Base")
                print(f"   - Пользователь не синхронизирован")
                print(f"   - Ошибка в регистре (попробуйте другой регистр)")
        
        except Exception as e:
            print(f"❌ Ошибка при проверке: {e}")


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования обработки username")
    print("=" * 80)
    
    await test_username_processing()
    await test_telegram_message_simulation()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 