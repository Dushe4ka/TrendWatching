#!/usr/bin/env python3
"""
Скрипт для обновления существующих ролей с новыми правами
"""

import asyncio
import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def update_existing_roles():
    """Обновление существующих ролей с новыми правами"""
    print("🔄 Обновление существующих ролей с новыми правами")
    print("=" * 50)
    
    try:
        # Подключаемся к MongoDB
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        client = MongoClient(mongo_uri)
        db = client.blackbox
        
        # Маппинг старых прав на новые
        permission_mapping = {
            "can_manage_sources": "can_access_sources",
            "can_use_analysis": "can_access_analysis",
            "can_receive_digest": "can_access_subscriptions",
            "can_auth_telegram": "can_manage_telegram_auth",
            "can_create_roles": "can_manage_roles",
            "can_manage_roles": "can_manage_roles"
        }
        
        # Получаем все роли
        print("📋 Получаем существующие роли...")
        existing_roles = list(db.roles.find({}))
        print(f"✅ Найдено {len(existing_roles)} ролей")
        
        for role in existing_roles:
            role_name = role.get("name") or role.get("role_name")
            print(f"\n🔄 Обновление роли '{role_name}'...")
            
            # Получаем старые права
            old_permissions = role.get("permissions", {})
            print(f"   Старые права: {old_permissions}")
            
            # Создаем новые права
            new_permissions = {
                "can_access_sources": False,
                "can_access_analysis": False,
                "can_access_subscriptions": False,
                "can_manage_roles": False,
                "can_manage_users": False,
                "can_manage_telegram_auth": False
            }
            
            # Маппим старые права на новые
            for old_perm, new_perm in permission_mapping.items():
                if old_perm in old_permissions and old_permissions[old_perm]:
                    new_permissions[new_perm] = True
                    print(f"   ✅ {old_perm} -> {new_perm}")
            
            # Специальная обработка для роли tester
            if role_name == "tester":
                new_permissions.update({
                    "can_access_sources": True,
                    "can_access_analysis": True,
                    "can_access_subscriptions": True
                })
                print(f"   🔧 Специальные права для tester: источники, анализ, подписки")
            
            print(f"   Новые права: {new_permissions}")
            
            # Обновляем роль в базе
            update_data = {
                "permissions": new_permissions,
                "updated_at": "2025-08-21T14:20:00.000000"
            }
            
            # Обновляем по полю name
            result = db.roles.update_one(
                {"_id": role["_id"]},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print(f"   ✅ Роль '{role_name}' обновлена успешно")
            else:
                print(f"   ⚠️ Роль '{role_name}' не была обновлена")
        
        # Показываем обновленные роли
        print("\n📋 Обновленные роли:")
        for role in db.roles.find():
            role_name = role.get("name") or role.get("role_name")
            print(f"   🏷️ {role_name}: {role['description']}")
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
    print("🚀 Запуск обновления существующих ролей")
    print("=" * 50)
    
    await update_existing_roles()
    
    print("\n🏁 Обновление завершено")


if __name__ == "__main__":
    asyncio.run(main()) 