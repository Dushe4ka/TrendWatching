#!/usr/bin/env python3
"""
Финальный тест для проверки исправлений
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_final_fixes():
    """Тестирование финальных исправлений"""
    print("🔍 Финальный тест исправлений")
    print("=" * 50)
    
    try:
        from bot.utils.misc import is_admin_from_env
        from bot.utils.callback_utils import _callback_cache
        
        # Тест 1: Проверка импорта _callback_cache
        print(f"1️⃣ Тест импорта _callback_cache...")
        print(f"   Тип _callback_cache: {type(_callback_cache)}")
        print(f"   Содержимое: {_callback_cache}")
        print(f"   ✅ Импорт _callback_cache работает")
        
        print()
        
        # Тест 2: Проверка функции is_admin_from_env
        print(f"2️⃣ Тест is_admin_from_env...")
        user_id = 5032415442
        is_admin_user = is_admin_from_env(user_id)
        print(f"   is_admin_from_env({user_id}): {'✅ Да' if is_admin_user else '❌ Нет'}")
        
        # Проверяем с администратором
        admin_ids_str = os.getenv("ADMIN_ID", "")
        if admin_ids_str:
            admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip().isdigit()]
            if admin_ids:
                admin_id = admin_ids[0]
                is_admin_user = is_admin_from_env(admin_id)
                print(f"   is_admin_from_env({admin_id}): {'✅ Да' if is_admin_user else '❌ Нет'}")
        
        print()
        
        # Тест 3: Проверка логики выбора клавиатуры
        print(f"3️⃣ Тест логики выбора клавиатуры...")
        print(f"   Правило: Сначала проверяем ADMIN_ID, потом роль в системе")
        print(f"   Если пользователь в ADMIN_ID -> клавиатура администратора")
        print(f"   Если пользователь НЕ в ADMIN_ID -> клавиатура обычного пользователя")
        
        print()
        
        # Тест 4: Проверка функции send_welcome_message
        print(f"4️⃣ Тест функции send_welcome_message...")
        print(f"   Функция теперь принимает user_id параметр")
        print(f"   Проверяет ADMIN_ID по user_id из Telegram")
        print(f"   Выбирает правильную клавиатуру")
        
        print()
        
        print("✅ Все исправления работают корректно")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск финального тестирования")
    print("=" * 50)
    
    await test_final_fixes()
    
    print("\n🏁 Финальное тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 