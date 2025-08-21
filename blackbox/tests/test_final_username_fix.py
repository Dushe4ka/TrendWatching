#!/usr/bin/env python3
"""
Финальный тест для проверки исправленной системы с username
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_final_username_system():
    """Тестирование финальной системы с username"""
    print("🔍 Финальный тест системы с username")
    print("=" * 60)
    
    try:
        from bot.utils.misc import check_user_access
        
        # Тестируем с пользователем @SHIFYuu
        user_id = 5032415442
        username = "SHIFYuu"
        
        print(f"🔍 Тестирование пользователя @{username} (ID: {user_id})")
        print("-" * 50)
        
        # Тест 1: Проверка доступа с username
        print(f"1️⃣ Тест check_user_access с username...")
        access_granted, message, role = await check_user_access(user_id, username)
        print(f"   Результат: {'✅ Доступ разрешен' if access_granted else '❌ Доступ запрещен'}")
        print(f"   Сообщение: {message}")
        print(f"   Роль: {role}")
        
        print()
        
        # Тест 2: Проверка доступа без username (должен использовать старую логику)
        print(f"2️⃣ Тест check_user_access БЕЗ username...")
        access_granted, message, role = await check_user_access(user_id, None)
        print(f"   Результат: {'✅ Доступ разрешен' if access_granted else '❌ Доступ запрещен'}")
        print(f"   Сообщение: {message}")
        print(f"   Роль: {role}")
        
        print()
        
        # Тест 3: Проверка с несуществующим пользователем
        print(f"3️⃣ Тест с несуществующим пользователем @test_user...")
        fake_user_id = 123456789
        fake_username = "test_user"
        
        access_granted, message, role = await check_user_access(fake_user_id, fake_username)
        print(f"   Результат: {'✅ Доступ разрешен' if access_granted else '❌ Доступ запрещен'}")
        print(f"   Сообщение: {message}")
        print(f"   Роль: {role}")
        
        print()
        
        # Тест 4: Проверка с уволенным пользователем
        print(f"4️⃣ Тест с уволенным пользователем @Lavkaaa_helper...")
        fired_user_id = 5032415442  # Тот же ID для теста
        fired_username = "Lavkaaa_helper"
        
        access_granted, message, role = await check_user_access(fired_user_id, fired_username)
        print(f"   Результат: {'✅ Доступ разрешен' if access_granted else '❌ Доступ запрещен'}")
        print(f"   Сообщение: {message}")
        print(f"   Роль: {role}")
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск финального тестирования с username")
    print("=" * 60)
    
    await test_final_username_system()
    
    print("\n🏁 Финальное тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 