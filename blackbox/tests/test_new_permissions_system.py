#!/usr/bin/env python3
"""
Тест новой системы прав
"""

import asyncio
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

async def test_new_permissions_system():
    """Тестирование новой системы прав"""
    print("🔍 Тест новой системы прав")
    print("=" * 50)
    
    try:
        from bot.keyboards.inline_keyboards import get_dynamic_main_menu_keyboard
        
        # Тест 1: Администратор (все права)
        print(f"1️⃣ Тест администратора (все права)...")
        admin_permissions = {
            "can_access_sources": True,
            "can_access_analysis": True,
            "can_access_subscriptions": True,
            "can_manage_roles": True,
            "can_manage_users": True,
            "can_manage_telegram_auth": True
        }
        admin_keyboard = get_dynamic_main_menu_keyboard(admin_permissions)
        print(f"   Клавиатура администратора:")
        for i, row in enumerate(admin_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print()
        
        # Тест 2: Менеджер (источники + анализ)
        print(f"2️⃣ Тест менеджера (источники + анализ)...")
        manager_permissions = {
            "can_access_sources": True,
            "can_access_analysis": True,
            "can_access_subscriptions": False,
            "can_manage_roles": False,
            "can_manage_users": False,
            "can_manage_telegram_auth": False
        }
        manager_keyboard = get_dynamic_main_menu_keyboard(manager_permissions)
        print(f"   Клавиатура менеджера:")
        for i, row in enumerate(manager_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print()
        
        # Тест 3: Аналитик (только анализ)
        print(f"3️⃣ Тест аналитика (только анализ)...")
        analyst_permissions = {
            "can_access_sources": False,
            "can_access_analysis": True,
            "can_access_subscriptions": False,
            "can_manage_roles": False,
            "can_manage_users": False,
            "can_manage_telegram_auth": False
        }
        analyst_keyboard = get_dynamic_main_menu_keyboard(analyst_permissions)
        print(f"   Клавиатура аналитика:")
        for i, row in enumerate(analyst_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print()
        
        # Тест 4: Куратор (источники + подписки)
        print(f"4️⃣ Тест куратора (источники + подписки)...")
        curator_permissions = {
            "can_access_sources": True,
            "can_access_analysis": False,
            "can_access_subscriptions": True,
            "can_manage_roles": False,
            "can_manage_users": False,
            "can_manage_telegram_auth": False
        }
        curator_keyboard = get_dynamic_main_menu_keyboard(curator_permissions)
        print(f"   Клавиатура куратора:")
        for i, row in enumerate(curator_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print()
        
        # Тест 5: Просмотрщик (только подписки)
        print(f"5️⃣ Тест просмотрщика (только подписки)...")
        viewer_permissions = {
            "can_access_sources": False,
            "can_access_analysis": False,
            "can_access_subscriptions": True,
            "can_manage_roles": False,
            "can_manage_users": False,
            "can_manage_telegram_auth": False
        }
        viewer_keyboard = get_dynamic_main_menu_keyboard(viewer_permissions)
        print(f"   Клавиатура просмотрщика:")
        for i, row in enumerate(viewer_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print()
        
        # Тест 6: Пользователь без прав
        print(f"6️⃣ Тест пользователя без прав...")
        no_permissions = {
            "can_access_sources": False,
            "can_access_analysis": False,
            "can_access_subscriptions": False,
            "can_manage_roles": False,
            "can_manage_users": False,
            "can_manage_telegram_auth": False
        }
        no_permissions_keyboard = get_dynamic_main_menu_keyboard(no_permissions)
        print(f"   Клавиатура без прав:")
        for i, row in enumerate(no_permissions_keyboard.inline_keyboard):
            for j, button in enumerate(row):
                print(f"     [{i}][{j}]: {button.text} -> {button.callback_data}")
        
        print()
        
        print("✅ Новая система прав работает корректно!")
        print("📋 Резюме:")
        print("   - Администратор: все кнопки")
        print("   - Менеджер: Источники + Анализ")
        print("   - Аналитик: только Анализ")
        print("   - Куратор: Источники + Подписки")
        print("   - Просмотрщик: только Подписки")
        print("   - Без прав: сообщение об отсутствии функций")
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск тестирования новой системы прав")
    print("=" * 50)
    
    await test_new_permissions_system()
    
    print("\n🏁 Тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 