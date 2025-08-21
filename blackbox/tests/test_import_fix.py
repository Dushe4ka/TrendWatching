#!/usr/bin/env python3
"""
Быстрый тест для проверки исправления импорта
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_import_fix():
    """Тестирование исправления импорта"""
    print("🔍 Тест исправления импорта")
    print("=" * 40)
    
    try:
        from bot.utils.misc import is_admin_from_env
        
        # Тестируем функцию
        user_id = 5032415442
        is_admin_user = is_admin_from_env(user_id)
        print(f"✅ is_admin_from_env({user_id}): {'Да' if is_admin_user else 'Нет'}")
        
        # Тестируем с администратором
        admin_ids_str = os.getenv("ADMIN_ID", "")
        if admin_ids_str:
            admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip().isdigit()]
            if admin_ids:
                admin_id = admin_ids[0]
                is_admin_user = is_admin_from_env(admin_id)
                print(f"✅ is_admin_from_env({admin_id}): {'Да' if is_admin_user else 'Нет'}")
        
        print("✅ Импорт работает корректно")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования исправления импорта")
    print("=" * 40)
    
    await test_import_fix()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 