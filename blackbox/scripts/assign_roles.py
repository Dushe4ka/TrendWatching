#!/usr/bin/env python3
"""
Скрипт для назначения ролей пользователям в Lark Base
"""

import asyncio
import sys
import os
import argparse
from typing import Dict, List, Optional

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_role_system_config
from role_model.lark_provider import LarkUserProvider, LarkRoleProvider
from role_model.role_manager import RoleManager


class RoleAssigner:
    """Класс для назначения ролей пользователям"""
    
    def __init__(self):
        role_config = get_role_system_config()["lark"]
        self.user_provider = LarkUserProvider(
            app_id=role_config["app_id"],
            app_secret=role_config["app_secret"],
            table_app_id=role_config["table_app_id"],
            table_id=role_config["table_id"]
        )
        self.role_provider = LarkRoleProvider()
        self.role_manager = RoleManager(self.user_provider, self.role_provider)
    
    async def get_all_users(self) -> List[dict]:
        """Получить всех пользователей"""
        users = await self.role_manager.get_all_users()
        return [
            {
                'user_id': user.user_id,
                'username': user.telegram_username,
                'role': user.role,
                'company': user.company_id
            }
            for user in users
        ]
    
    async def get_users_without_roles(self) -> List[dict]:
        """Получить пользователей без ролей"""
        users = await self.get_all_users()
        return [user for user in users if not user['role']]
    
    async def get_users_by_role(self, role: str) -> List[dict]:
        """Получить пользователей с определенной ролью"""
        users = await self.get_all_users()
        return [user for user in users if user['role'] == role]
    
    async def get_available_roles(self) -> List[str]:
        """Получить доступные роли"""
        roles = await self.role_manager.get_all_roles()
        return [role.role_name for role in roles]
    
    async def assign_role_to_user(self, username: str, role: str) -> bool:
        """Назначить роль пользователю (заглушка - требует реализации в Lark API)"""
        print(f"⚠️  Назначение роли '{role}' пользователю @{username}")
        print("   Для полной реализации требуется интеграция с Lark API для обновления записей")
        print("   Сейчас это только симуляция")
        return True
    
    async def show_user_statistics(self):
        """Показать статистику пользователей"""
        users = await self.get_all_users()
        roles = await self.get_available_roles()
        
        print("📊 Статистика пользователей:")
        print("=" * 40)
        print(f"Всего пользователей: {len(users)}")
        
        # Статистика по ролям
        role_stats = {}
        for user in users:
            role = user['role'] or 'Без роли'
            role_stats[role] = role_stats.get(role, 0) + 1
        
        print("\nРаспределение по ролям:")
        for role, count in sorted(role_stats.items()):
            print(f"  {role}: {count} пользователей")
        
        print(f"\nДоступные роли: {', '.join(roles)}")
    
    async def show_users_without_roles(self):
        """Показать пользователей без ролей"""
        users_without_roles = await self.get_users_without_roles()
        
        print(f"👥 Пользователи без ролей ({len(users_without_roles)}):")
        print("=" * 50)
        
        for i, user in enumerate(users_without_roles[:20], 1):
            print(f"{i:2d}. @{user['username']} (ID: {user['user_id']})")
        
        if len(users_without_roles) > 20:
            print(f"... и еще {len(users_without_roles) - 20} пользователей")
    
    async def show_users_by_role(self, role: str):
        """Показать пользователей с определенной ролью"""
        users = await self.get_users_by_role(role)
        
        print(f"👥 Пользователи с ролью '{role}' ({len(users)}):")
        print("=" * 50)
        
        for i, user in enumerate(users[:20], 1):
            print(f"{i:2d}. @{user['username']} (ID: {user['user_id']})")
        
        if len(users) > 20:
            print(f"... и еще {len(users) - 20} пользователей")
    
    async def interactive_role_assignment(self):
        """Интерактивное назначение ролей"""
        print("🎯 Интерактивное назначение ролей")
        print("=" * 40)
        
        # Получаем пользователей без ролей
        users_without_roles = await self.get_users_without_roles()
        
        if not users_without_roles:
            print("✅ Все пользователи уже имеют роли!")
            return
        
        # Получаем доступные роли
        roles = await self.get_available_roles()
        
        print(f"Найдено {len(users_without_roles)} пользователей без ролей")
        print(f"Доступные роли: {', '.join(roles)}")
        print()
        
        # Показываем первых 10 пользователей
        print("Первые 10 пользователей без ролей:")
        for i, user in enumerate(users_without_roles[:10], 1):
            print(f"{i:2d}. @{user['username']}")
        
        print()
        print("Для назначения роли введите: username role")
        print("Например: Romka201616 analyst")
        print("Для выхода введите: exit")
        print()
        
        while True:
            try:
                command = input("> ").strip()
                
                if command.lower() == 'exit':
                    break
                
                if not command:
                    continue
                
                parts = command.split()
                if len(parts) != 2:
                    print("❌ Неверный формат. Используйте: username role")
                    continue
                
                username, role = parts
                
                # Убираем @ если есть
                if username.startswith('@'):
                    username = username[1:]
                
                # Проверяем существование роли
                if role not in roles:
                    print(f"❌ Роль '{role}' не существует. Доступные роли: {', '.join(roles)}")
                    continue
                
                # Проверяем существование пользователя
                user_exists = any(u['username'] == username for u in users_without_roles)
                if not user_exists:
                    print(f"❌ Пользователь @{username} не найден среди пользователей без ролей")
                    continue
                
                # Назначаем роль
                success = await self.assign_role_to_user(username, role)
                if success:
                    print(f"✅ Роль '{role}' назначена пользователю @{username}")
                else:
                    print(f"❌ Ошибка при назначении роли")
                
            except KeyboardInterrupt:
                print("\n👋 Выход из интерактивного режима")
                break
            except Exception as e:
                print(f"❌ Ошибка: {str(e)}")


async def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Назначение ролей пользователям")
    parser.add_argument("--stats", action="store_true", help="Показать статистику пользователей")
    parser.add_argument("--no-roles", action="store_true", help="Показать пользователей без ролей")
    parser.add_argument("--by-role", type=str, help="Показать пользователей с определенной ролью")
    parser.add_argument("--interactive", action="store_true", help="Интерактивное назначение ролей")
    
    args = parser.parse_args()
    
    assigner = RoleAssigner()
    
    try:
        if args.stats:
            await assigner.show_user_statistics()
        elif args.no_roles:
            await assigner.show_users_without_roles()
        elif args.by_role:
            await assigner.show_users_by_role(args.by_role)
        elif args.interactive:
            await assigner.interactive_role_assignment()
        else:
            # По умолчанию показываем статистику
            await assigner.show_user_statistics()
            print()
            await assigner.show_users_without_roles()
    
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 