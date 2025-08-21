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

async def test_final_system():
    """Тестирование финальной системы"""
    print("🔍 Финальный тест системы с username")
    print("=" * 60)
    
    try:
        from bot.utils.misc import get_role_manager_async
        
        # Получаем ролевой менеджер
        role_manager = await get_role_manager_async()
        if not role_manager:
            print("❌ RoleManager недоступен")
            return
        
        print("✅ RoleManager получен")
        print()
        
        # Тестируем с пользователем @SHIFYuu
        username = "SHIFYuu"
        user_id = 5032415442  # Фиктивный ID для теста
        
        print(f"🔍 Тестирование пользователя @{username}")
        print("-" * 50)
        
        # Тест 1: Проверка доступа
        print(f"1️⃣ Тест check_user_access...")
        access_granted, message = await role_manager.check_user_access(username)
        print(f"   Результат: {'✅ Доступ разрешен' if access_granted else '❌ Доступ запрещен'}")
        print(f"   Сообщение: {message}")
        
        # Тест 2: Получение разрешений
        print(f"2️⃣ Тест get_user_permissions_by_username...")
        permissions = await role_manager.get_user_permissions_by_username(username)
        print(f"   Разрешения: {permissions}")
        
        # Тест 3: Проверка конкретного разрешения
        print(f"3️⃣ Тест check_permission...")
        has_permission = await role_manager.check_permission(user_id, "can_use_analysis", username)
        print(f"   can_use_analysis: {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
        
        has_permission = await role_manager.check_permission(user_id, "can_manage_sources", username)
        print(f"   can_manage_sources: {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
        
        has_permission = await role_manager.check_permission(user_id, "can_receive_digest", username)
        print(f"   can_receive_digest: {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
        
        print()
        
        # Тест 4: Проверка с несуществующим пользователем
        print(f"4️⃣ Тест с несуществующим пользователем @test_user")
        print("-" * 50)
        
        fake_username = "test_user"
        fake_user_id = 123456789
        
        access_granted, message = await role_manager.check_user_access(fake_username)
        print(f"   Доступ: {'✅ Разрешен' if access_granted else '❌ Запрещен'}")
        print(f"   Сообщение: {message}")
        
        permissions = await role_manager.get_user_permissions_by_username(fake_username)
        print(f"   Разрешения: {permissions}")
        
        has_permission = await role_manager.check_permission(fake_user_id, "can_use_analysis", fake_username)
        print(f"   can_use_analysis: {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
        
        print()
        
        # Тест 5: Проверка с пользователем со статусом "Уволен"
        print(f"5️⃣ Тест с пользователем @Lavkaaa_helper (статус 'Уволен')")
        print("-" * 50)
        
        fired_username = "Lavkaaa_helper"
        fired_user_id = 5032415442  # Тот же ID для теста
        
        access_granted, message = await role_manager.check_user_access(fired_username)
        print(f"   Доступ: {'✅ Разрешен' if access_granted else '❌ Запрещен'}")
        print(f"   Сообщение: {message}")
        
        permissions = await role_manager.get_user_permissions_by_username(fired_username)
        print(f"   Разрешения: {permissions}")
        
        has_permission = await role_manager.check_permission(fired_user_id, "can_use_analysis", fired_username)
        print(f"   can_use_analysis: {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск финального тестирования")
    print("=" * 60)
    
    await test_final_system()
    
    print("\n🏁 Финальное тестирование завершено")


if __name__ == "__main__":
    asyncio.run(main()) 