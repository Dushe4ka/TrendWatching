#!/usr/bin/env python3
"""
Скрипт для обновления ролей и прав в MongoDB
"""

import asyncio
import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def update_roles_permissions():
    """Обновление ролей и прав в MongoDB"""
    print("🔄 Обновление ролей и прав в MongoDB")
    print("=" * 50)
    
    try:
        # Подключаемся к MongoDB
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        client = MongoClient(mongo_uri)
        db = client.blackbox
        
        # Удаляем старые роли
        print("🗑️ Удаляем старые роли...")
        db.roles.delete_many({})
        print("✅ Старые роли удалены")
        
        # Создаем новые роли с новыми правами
        new_roles = [
            {
                "name": "admin",
                "description": "Полный доступ ко всем функциям",
                "permissions": {
                    "can_access_sources": True,
                    "can_access_analysis": True,
                    "can_access_subscriptions": True,
                    "can_manage_roles": True,
                    "can_manage_users": True,
                    "can_manage_telegram_auth": True
                }
            },
            {
                "name": "manager",
                "description": "Менеджер с доступом к источникам и анализу",
                "permissions": {
                    "can_access_sources": True,
                    "can_access_analysis": True,
                    "can_access_subscriptions": False,
                    "can_manage_roles": False,
                    "can_manage_users": False,
                    "can_manage_telegram_auth": False
                }
            },
            {
                "name": "analyst",
                "description": "Аналитик с доступом только к анализу",
                "permissions": {
                    "can_access_sources": False,
                    "can_access_analysis": True,
                    "can_access_subscriptions": False,
                    "can_manage_roles": False,
                    "can_manage_users": False,
                    "can_manage_telegram_auth": False
                }
            },
            {
                "name": "curator",
                "description": "Куратор с доступом к источникам и подпискам",
                "permissions": {
                    "can_access_sources": True,
                    "can_access_analysis": False,
                    "can_access_subscriptions": True,
                    "can_manage_roles": False,
                    "can_manage_users": False,
                    "can_manage_telegram_auth": False
                }
            },
            {
                "name": "viewer",
                "description": "Просмотрщик с доступом только к подпискам",
                "permissions": {
                    "can_access_sources": False,
                    "can_access_analysis": False,
                    "can_access_subscriptions": True,
                    "can_manage_roles": False,
                    "can_manage_users": False,
                    "can_manage_telegram_auth": False
                }
            },
            {
                "name": "tester",
                "description": "Тестер с полным доступом к основным функциям",
                "permissions": {
                    "can_access_sources": True,
                    "can_access_analysis": True,
                    "can_access_subscriptions": True,
                    "can_manage_roles": False,
                    "can_manage_users": False,
                    "can_manage_telegram_auth": False
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
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении ролей: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Основная функция"""
    print("🚀 Запуск обновления ролей и прав")
    print("=" * 50)
    
    await update_roles_permissions()
    
    print("\n🏁 Обновление завершено")


if __name__ == "__main__":
    asyncio.run(main()) 