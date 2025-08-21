#!/usr/bin/env python3
"""
Тест для проверки исправления отображения ролей и клавиатур
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_role_display_fix():
    """Тестирование исправления отображения ролей"""
    print("🔍 Тест исправления отображения ролей и клавиатур")
    print("=" * 60)
    
    try:
        from bot.utils.misc import get_user_info, is_admin
        from bot.keyboards.inline_keyboards import get_user_main_menu_keyboard, get_admin_main_menu_keyboard
        
        # Тестируем с пользователем @SHIFYuu
        user_id = 5032415442
        username = "SHIFYuu"
        
        print(f"🔍 Тестирование пользователя @{username} (ID: {user_id})")
        print("-" * 50)
        
        # Тест 1: Получение информации о пользователе с username
        print(f"1️⃣ Тест get_user_info с username...")
        user_info = await get_user_info(user_id, username)
        
        if user_info:
            print(f"✅ Информация о пользователе найдена:")
            print(f"   - ID: {user_info.user_id}")
            print(f"   - Username: @{user_info.telegram_username}")
            print(f"   - Имя: {user_info.employee_name}")
            print(f"   - Роль: {user_info.role}")
            print(f"   - Статус: {'Активен' if user_info.is_active else 'Неактивен'}")
            print(f"   - Статус сотрудника: {user_info.employee_status}")
        else:
            print(f"❌ Информация о пользователе НЕ найдена")
        
        print()
        
        # Тест 2: Проверка прав администратора
        print(f"2️⃣ Тест is_admin...")
        is_admin_user = await is_admin(user_id)
        print(f"   Результат: {'✅ Администратор' if is_admin_user else '❌ Не администратор'}")
        
        print()
        
        # Тест 3: Проверка клавиатур
        print(f"3️⃣ Тест клавиатур...")
        
        # Клавиатура обычного пользователя
        user_keyboard = get_user_main_menu_keyboard()
        print(f"   Клавиатура обычного пользователя:")
        for i, row in enumerate(user_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print()
        
        # Клавиатура администратора
        admin_keyboard = get_admin_main_menu_keyboard()
        print(f"   Клавиатура администратора:")
        for i, row in enumerate(admin_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print()
        
        # Тест 4: Проверка с несуществующим пользователем
        print(f"4️⃣ Тест с несуществующим пользователем @test_user...")
        fake_user_id = 123456789
        fake_username = "test_user"
        
        user_info = await get_user_info(fake_user_id, fake_username)
        if user_info:
            print(f"✅ Информация о пользователе найдена (неожиданно)")
        else:
            print(f"❌ Информация о пользователе НЕ найдена (ожидаемо)")
        
        print()
        
        # Тест 5: Проверка с уволенным пользователем
        print(f"5️⃣ Тест с уволенным пользователем @Lavkaaa_helper...")
        fired_user_id = 5032415442  # Тот же ID для теста
        fired_username = "Lavkaaa_helper"
        
        user_info = await get_user_info(fired_user_id, fired_username)
        if user_info:
            print(f"✅ Информация о пользователе найдена:")
            print(f"   - Роль: {user_info.role}")
            print(f"   - Статус сотрудника: {user_info.employee_status}")
        else:
            print(f"❌ Информация о пользователе НЕ найдена")
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования исправления отображения ролей")
    print("=" * 60)
    
    await test_role_display_fix()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 