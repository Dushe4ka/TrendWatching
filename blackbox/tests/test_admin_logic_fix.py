#!/usr/bin/env python3
"""
Тест для проверки правильной логики администратора
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_admin_logic_fix():
    """Тестирование правильной логики администратора"""
    print("🔍 Тест правильной логики администратора")
    print("=" * 60)
    
    try:
        from bot.utils.misc import is_admin_from_env, get_user_info
        from bot.keyboards.inline_keyboards import get_user_main_menu_keyboard, get_admin_main_menu_keyboard
        
        # Получаем список администраторов из переменной окружения
        admin_ids_str = os.getenv("ADMIN_ID", "")
        if admin_ids_str:
            admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip().isdigit()]
            print(f"🔧 Администраторы из ADMIN_ID: {admin_ids}")
        else:
            print("⚠️ Переменная окружения ADMIN_ID не установлена")
            admin_ids = []
        
        print()
        
        # Тест 1: Проверка администратора из ADMIN_ID
        if admin_ids:
            admin_id = admin_ids[0]
            print(f"1️⃣ Тест администратора из ADMIN_ID (ID: {admin_id})...")
            
            # Проверяем функцию is_admin_from_env
            is_admin_user = is_admin_from_env(admin_id)
            print(f"   is_admin_from_env({admin_id}): {'✅ Да' if is_admin_user else '❌ Нет'}")
            
            # Проверяем клавиатуру
            if is_admin_user:
                keyboard = get_admin_main_menu_keyboard()
                print(f"   Клавиатура: Администраторская (с кнопками Авторизация и Админ)")
            else:
                keyboard = get_user_main_menu_keyboard()
                print(f"   Клавиатура: Обычная (без кнопок Авторизация и Админ)")
        
        print()
        
        # Тест 2: Проверка обычного пользователя
        print(f"2️⃣ Тест обычного пользователя @SHIFYuu...")
        user_id = 5032415442
        username = "SHIFYuu"
        
        # Проверяем функцию is_admin_from_env
        is_admin_user = is_admin_from_env(user_id)
        print(f"   is_admin_from_env({user_id}): {'✅ Да' if is_admin_user else '❌ Нет'}")
        
        # Получаем информацию о пользователе
        user_info = await get_user_info(user_id, username)
        if user_info:
            print(f"   Роль в системе: {user_info.role}")
        else:
            print(f"   Роль в системе: Не найдена")
        
        # Проверяем клавиатуру
        if is_admin_user:
            keyboard = get_admin_main_menu_keyboard()
            print(f"   Клавиатура: Администраторская (с кнопками Авторизация и Админ)")
        else:
            keyboard = get_user_main_menu_keyboard()
            print(f"   Клавиатура: Обычная (без кнопок Авторизация и Админ)")
        
        print()
        
        # Тест 3: Проверка несуществующего пользователя
        print(f"3️⃣ Тест несуществующего пользователя @test_user...")
        fake_user_id = 123456789
        fake_username = "test_user"
        
        # Проверяем функцию is_admin_from_env
        is_admin_user = is_admin_from_env(fake_user_id)
        print(f"   is_admin_from_env({fake_user_id}): {'✅ Да' if is_admin_user else '❌ Нет'}")
        
        # Проверяем клавиатуру
        if is_admin_user:
            keyboard = get_admin_main_menu_keyboard()
            print(f"   Клавиатура: Администраторская (с кнопками Авторизация и Админ)")
        else:
            keyboard = get_user_main_menu_keyboard()
            print(f"   Клавиатура: Обычная (без кнопок Авторизация и Админ)")
        
        print()
        
        # Тест 4: Сравнение клавиатур
        print(f"4️⃣ Сравнение клавиатур...")
        
        user_keyboard = get_user_main_menu_keyboard()
        admin_keyboard = get_admin_main_menu_keyboard()
        
        print(f"   Клавиатура обычного пользователя:")
        for i, row in enumerate(user_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print(f"   Клавиатура администратора:")
        for i, row in enumerate(admin_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print()
        
        # Тест 5: Логика выбора клавиатуры
        print(f"5️⃣ Логика выбора клавиатуры...")
        print(f"   Правило: Сначала проверяем ADMIN_ID, потом роль в системе")
        print(f"   Если пользователь в ADMIN_ID -> клавиатура администратора")
        print(f"   Если пользователь НЕ в ADMIN_ID -> клавиатура обычного пользователя")
        print(f"   Роль в системе НЕ влияет на выбор клавиатуры")
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования правильной логики администратора")
    print("=" * 60)
    
    await test_admin_logic_fix()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 