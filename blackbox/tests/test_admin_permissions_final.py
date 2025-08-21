#!/usr/bin/env python3
"""
Финальный тест исправленной логики админских прав
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

from bot.utils.misc import has_admin_permissions
from role_model.role_manager import RoleManager
from role_model.mongodb_provider import MongoDBRoleProvider
from role_model.lark_provider import LarkUserProvider

async def test_admin_permissions():
    """Тестирует исправленную логику админских прав"""
    
    print("🚀 Финальный тест исправленной логики админских прав")
    print("=" * 60)
    
    try:
        # Инициализируем провайдеры
        print("🔧 Инициализация провайдеров...")
        
        # MongoDB провайдер
        mongodb_provider = MongoDBRoleProvider()
        
        # Lark провайдер с переменными окружения
        lark_provider = LarkUserProvider(
            app_id=os.getenv("LARK_APP_ID"),
            app_secret=os.getenv("LARK_APP_SECRET"),
            table_app_id=os.getenv("LARK_TABLE_APP_ID"),
            table_id=os.getenv("LARK_TABLE_ID")
        )
        
        # Создаем ролевой менеджер
        role_manager = RoleManager(lark_provider, mongodb_provider)
        
        print("✅ Провайдеры инициализированы")
        
        # Тестируем пользователя с ролью tester
        test_username = "SHIFYuu"
        test_user_id = 5032415442
        
        print(f"\n🔍 Тестирование пользователя @{test_username} (ID: {test_user_id})")
        print("-" * 50)
        
        # Проверяем админские права
        print("🔍 Проверка админских прав...")
        has_admin = await has_admin_permissions(test_user_id, test_username)
        
        if has_admin:
            print("✅ Пользователь имеет админские права")
        else:
            print("❌ Пользователь НЕ имеет админских прав")
        
        # Получаем права пользователя
        print("\n🔍 Получение прав пользователя...")
        user_permissions = await role_manager.get_user_permissions_by_username(test_username)
        
        if user_permissions:
            print(f"✅ Права пользователя: {user_permissions}")
            
            # Проверяем конкретные админские права
            admin_permissions = [
                "can_manage_telegram_auth",
                "can_access_admin_panel"
            ]
            
            for perm in admin_permissions:
                has_perm = user_permissions.get(perm, False)
                status = "✅" if has_perm else "❌"
                print(f"{status} {perm}: {has_perm}")
        else:
            print("❌ Права пользователя не найдены")
        
        # Тестируем доступ к админским функциям
        print("\n🔍 Тестирование доступа к админским функциям...")
        
        # Проверяем доступ к управлению ролями
        can_manage_roles = user_permissions.get("can_access_admin_panel", False) if user_permissions else False
        print(f"🔧 Доступ к управлению ролями: {'✅' if can_manage_roles else '❌'}")
        
        # Проверяем доступ к управлению авторизацией
        can_manage_auth = user_permissions.get("can_manage_telegram_auth", False) if user_permissions else False
        print(f"🔐 Доступ к управлению авторизацией: {'✅' if can_manage_auth else '❌'}")
        
        # Проверяем доступ к Telegram каналам
        can_access_channels = user_permissions.get("can_access_admin_panel", False) if user_permissions else False
        print(f"📢 Доступ к Telegram каналам: {'✅' if can_access_channels else '❌'}")
        
        print("\n" + "=" * 60)
        print("🏁 Тестирование завершено")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_admin_permissions()) 