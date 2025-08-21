#!/usr/bin/env python3
"""
Скрипт для обновления ролей с упрощенной системой прав
"""

import asyncio
import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def update_roles_simplified():
    """Обновление ролей с упрощенной системой прав"""
    print("🔄 Обновление ролей с упрощенной системой прав")
    print("=" * 50)
    
    try:
        # Подключаемся к MongoDB
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        client = MongoClient(mongo_uri)
        db = client.blackbox
        
        # Удаляем ВСЕ роли
        print("🗑️ Удаляем все существующие роли...")
        result = db.roles.delete_many({})
        print(f"✅ Удалено {result.deleted_count} ролей")
        
        # Создаем новые роли с упрощенной системой прав
        new_roles = [
            {
                "name": "admin",
                "description": "Полный доступ ко всем функциям",
                "permissions": {
                    "can_access_sources": True,
                    "can_access_analysis": True,
                    "can_access_subscriptions": True,
                    "can_manage_telegram_auth": True,
                    "can_access_admin_panel": True
                }
            },
            {
                "name": "manager",
                "description": "Менеджер с доступом к источникам и анализу",
                "permissions": {
                    "can_access_sources": True,
                    "can_access_analysis": True,
                    "can_access_subscriptions": False,
                    "can_manage_telegram_auth": False,
                    "can_access_admin_panel": False
                }
            },
            {
                "name": "analyst",
                "description": "Аналитик с доступом только к анализу",
                "permissions": {
                    "can_access_sources": False,
                    "can_access_analysis": True,
                    "can_access_subscriptions": False,
                    "can_manage_telegram_auth": False,
                    "can_access_admin_panel": False
                }
            },
            {
                "name": "curator",
                "description": "Куратор с доступом к источникам и подпискам",
                "permissions": {
                    "can_access_sources": True,
                    "can_access_analysis": False,
                    "can_access_subscriptions": True,
                    "can_manage_telegram_auth": False,
                    "can_access_admin_panel": False
                }
            },
            {
                "name": "viewer",
                "description": "Просмотрщик с доступом только к подпискам",
                "permissions": {
                    "can_access_sources": False,
                    "can_access_analysis": False,
                    "can_access_subscriptions": True,
                    "can_manage_telegram_auth": False,
                    "can_access_admin_panel": False
                }
            },
            {
                "name": "tester",
                "description": "Тестер с полным доступом к основным функциям",
                "permissions": {
                    "can_access_sources": True,
                    "can_access_analysis": True,
                    "can_access_subscriptions": True,
                    "can_manage_telegram_auth": False,
                    "can_access_admin_panel": False
                }
            }
        ]
        
        # Вставляем новые роли
        print("➕ Создаем новые роли...")
        result = db.roles.insert_many(new_roles)
        print(f"✅ Создано {len(result.inserted_ids)} ролей")
        
        # Показываем созданные роли
        print("\n📋 Созданные роли:")
        for role in db.roles.find():
            print(f"   🏷️ {role['name']}: {role['description']}")
            print(f"      Права:")
            for permission, value in role['permissions'].items():
                status = "✅" if value else "❌"
                print(f"        {status} {permission}")
            print()
        
        print("🎉 Обновление ролей завершено успешно!")
        print("\n📋 Новая система прав:")
        print("   - can_access_sources: Доступ к источникам")
        print("   - can_access_analysis: Доступ к анализу")
        print("   - can_access_subscriptions: Доступ к подпискам")
        print("   - can_manage_telegram_auth: Управление авторизацией")
        print("   - can_access_admin_panel: Доступ к админ панели (все админские функции)")
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении ролей: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск обновления ролей с упрощенной системой прав")
    print("=" * 50)
    
    await update_roles_simplified()
    
    print("\n🏁 Обновление завершено")


if __name__ == "__main__":
    asyncio.run(main()) 