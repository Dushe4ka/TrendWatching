from typing import Dict, List, Optional, Callable
from .base_provider import BaseUserProvider, BaseRoleProvider, UserInfo, RolePermissions


class RoleManager:
    """Менеджер ролей для управления доступом к функциям бота"""
    
    def __init__(self, user_provider: BaseUserProvider, role_provider: BaseRoleProvider):
        self.user_provider = user_provider
        self.role_provider = role_provider
        self._permission_handlers: Dict[str, Callable] = {}
    
    def register_permission_handler(self, permission: str, handler: Callable):
        """Зарегистрировать обработчик для проверки разрешения"""
        self._permission_handlers[permission] = handler
    
    async def check_permission(self, user_id: int, permission: str, username: str = None) -> bool:
        """Проверить разрешение для пользователя"""
        print(f"🔍 [DEBUG] Проверка разрешения '{permission}' для пользователя ID: {user_id}")
        if username:
            print(f"📱 [DEBUG] Username из Telegram: @{username}")
        
        # Если у нас есть username, используем его напрямую
        if username:
            print(f"🔍 [DEBUG] Используем username для проверки разрешения: @{username}")
            
            # Проверяем доступ через username
            print(f"🔍 [DEBUG] Проверка доступа для username: @{username}")
            access_granted, error_message = await self.check_user_access(username)
            if not access_granted:
                print(f"❌ [DEBUG] Доступ НЕ разрешен: {error_message}")
                return False
            print(f"✅ [DEBUG] Доступ разрешен для @{username}")
            
            # Получаем информацию о пользователе по username
            user_info = await self.get_user_by_username(username)
            if not user_info:
                print(f"❌ [DEBUG] Пользователь @{username} не найден в системе")
                return False
            
            print(f"🔍 [DEBUG] Информация о пользователе: {user_info}")
            
            # Получаем роль пользователя
            role = user_info.role
            if not role:
                print(f"❌ [DEBUG] У пользователя @{username} не назначена роль")
                return False
            
            print(f"🔍 [DEBUG] Роль пользователя: {role}")
            
            # Получаем разрешения для роли
            role_permissions = await self.role_provider.get_role_permissions(role)
            if not role_permissions:
                print(f"❌ [DEBUG] Роль '{role}' не найдена в системе")
                return False
            
            print(f"🔍 [DEBUG] Разрешения роли '{role}': {role_permissions.permissions}")
            
            # Проверяем конкретное разрешение
            has_permission = role_permissions.permissions.get(permission, False)
            print(f"🔍 [DEBUG] Разрешение '{permission}': {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
            
            return has_permission
        
        # Если username нет, используем старую логику через ID
        print(f"🔍 [DEBUG] Username не предоставлен, используем поиск по ID")
        
        # Получаем информацию о пользователе
        user_info = await self.user_provider.get_user_info(user_id)
        if not user_info:
            print(f"❌ [DEBUG] Пользователь ID {user_id} не найден в системе")
            return False
        
        print(f"🔍 [DEBUG] Информация о пользователе: {user_info}")
        
        # Проверяем доступ через новую логику
        if user_info.telegram_username:
            print(f"🔍 [DEBUG] Проверка доступа для username: @{user_info.telegram_username}")
            access_granted, error_message = await self.check_user_access(user_info.telegram_username)
            if not access_granted:
                print(f"❌ [DEBUG] Доступ НЕ разрешен: {error_message}")
                return False
            print(f"✅ [DEBUG] Доступ разрешен для @{user_info.telegram_username}")
        else:
            print(f"❌ [DEBUG] У пользователя ID {user_id} нет telegram_username")
            return False
        
        # Получаем роль пользователя
        role = user_info.role
        if not role:
            print(f"❌ [DEBUG] У пользователя ID {user_id} не назначена роль")
            return False
        
        print(f"🔍 [DEBUG] Роль пользователя: {role}")
        
        # Получаем разрешения для роли
        role_permissions = await self.role_provider.get_role_permissions(role)
        if not role_permissions:
            print(f"❌ [DEBUG] Роль '{role}' не найдена в системе")
            return False
        
        print(f"🔍 [DEBUG] Разрешения роли '{role}': {role_permissions.permissions}")
        
        # Проверяем конкретное разрешение
        has_permission = role_permissions.permissions.get(permission, False)
        print(f"🔍 [DEBUG] Разрешение '{permission}': {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
        
        return has_permission
    
    async def get_user_permissions(self, user_id: int) -> Dict[str, bool]:
        """Получить все разрешения пользователя"""
        user_info = await self.user_provider.get_user_info(user_id)
        if not user_info or not user_info.is_whitelisted:
            return {}
        
        role_permissions = await self.role_provider.get_role_permissions(user_info.role)
        if not role_permissions:
            return {}
        
        return role_permissions.permissions.copy()
    
    async def get_user_permissions_by_username(self, username: str) -> Dict[str, bool]:
        """Получить все разрешения пользователя по username"""
        print(f"🔍 [DEBUG] Получение разрешений для пользователя @{username}")
        
        # Получаем информацию о пользователе по username
        user_info = await self.get_user_by_username(username)
        if not user_info:
            print(f"❌ [DEBUG] Пользователь @{username} не найден")
            return {}
        
        print(f"🔍 [DEBUG] Информация о пользователе @{username}: {user_info}")
        
        # Проверяем доступ через новую логику
        access_granted, error_message = await self.check_user_access(username)
        if not access_granted:
            print(f"❌ [DEBUG] Доступ НЕ разрешен для @{username}: {error_message}")
            return {}
        
        print(f"✅ [DEBUG] Доступ разрешен для @{username}")
        
        # Получаем разрешения для роли
        role_permissions = await self.role_provider.get_role_permissions(user_info.role)
        if not role_permissions:
            print(f"❌ [DEBUG] Роль '{user_info.role}' не найдена в системе")
            return {}
        
        print(f"🔍 [DEBUG] Разрешения роли '{user_info.role}': {role_permissions.permissions}")
        return role_permissions.permissions.copy()
    
    async def get_user_info(self, user_id: int) -> Optional[UserInfo]:
        """Получить информацию о пользователе"""
        return await self.user_provider.get_user_info(user_id)
    
    async def get_user_by_username(self, username: str) -> Optional[UserInfo]:
        """Получить информацию о пользователе по username"""
        if hasattr(self.user_provider, 'get_user_by_username'):
            return await self.user_provider.get_user_by_username(username)
        return None
    
    async def check_permission_by_username(self, username: str, permission: str) -> bool:
        """Проверить разрешение для пользователя по username"""
        user_info = await self.get_user_by_username(username)
        if not user_info:
            return False
        
        return await self.check_permission(user_info.user_id, permission)
    
    async def check_user_access(self, username: str) -> tuple[bool, str]:
        """Проверить доступ пользователя по username"""
        print(f"🔍 [DEBUG] RoleManager.check_user_access для username: @{username}")
        
        try:
            # Делегируем проверку в user_provider
            result = await self.user_provider.check_user_access(username)
            print(f"🔍 [DEBUG] Результат проверки доступа: {result}")
            return result
        except Exception as e:
            print(f"❌ [DEBUG] Ошибка в RoleManager.check_user_access: {e}")
            return False, f"❌ Ошибка проверки доступа: {e}"
    
    async def is_user_authorized(self, user_id: int) -> bool:
        """Проверить, авторизован ли пользователь"""
        user_info = await self.user_provider.get_user_info(user_id)
        if not user_info:
            return False
        
        # Проверяем через новую логику
        if user_info.telegram_username:
            access_granted, _ = await self.check_user_access(user_info.telegram_username)
            return access_granted
        
        return False
    
    async def get_user_role_info(self, user_id: int) -> Optional[RolePermissions]:
        """Получить информацию о роли пользователя"""
        user_info = await self.user_provider.get_user_info(user_id)
        if not user_info or not user_info.role:
            return None
        
        return await self.role_provider.get_role_permissions(user_info.role)
    
    async def get_role_permissions(self, role_name: str) -> Optional[Dict[str, bool]]:
        """Получить разрешения роли"""
        role_permissions = await self.role_provider.get_role_permissions(role_name)
        if not role_permissions:
            return None
        
        return role_permissions.permissions.copy()
    
    async def get_all_roles(self) -> List[RolePermissions]:
        """Получить все роли"""
        return await self.role_provider.get_all_roles()
    
    async def create_role(self, role_name: str, permissions: Dict[str, bool], description: str = "") -> bool:
        """Создать новую роль"""
        return await self.role_provider.create_role(role_name, permissions, description)
    
    async def update_role(self, role_name: str, permissions: Dict[str, bool], description: str = "") -> bool:
        """Обновить роль"""
        return await self.role_provider.update_role(role_name, permissions, description)
    
    async def delete_role(self, role_name: str) -> bool:
        """Удалить роль"""
        return await self.role_provider.delete_role(role_name)
    
    async def role_exists(self, role_name: str) -> bool:
        """Проверить существование роли"""
        return await self.role_provider.role_exists(role_name)
    
    async def get_all_users(self) -> List[UserInfo]:
        """Получить всех пользователей"""
        return await self.user_provider.get_all_users()
    
    async def get_users_by_role(self, role_name: str) -> List[UserInfo]:
        """Получить пользователей с определенной ролью"""
        all_users = await self.user_provider.get_all_users()
        return [user for user in all_users if user.role == role_name]
    
    async def get_available_permissions(self) -> List[str]:
        """Получить список всех доступных разрешений"""
        return [
            "can_access_sources",
            "can_access_analysis",
            "can_access_subscriptions",
            "can_manage_telegram_auth",
            "can_access_admin_panel"
        ]
    
    async def get_permission_description(self, permission: str) -> str:
        """Получить описание разрешения"""
        descriptions = {
            "can_access_sources": "Доступ к источникам",
            "can_access_analysis": "Доступ к анализу",
            "can_access_subscriptions": "Доступ к подпискам",
            "can_manage_telegram_auth": "Управление авторизацией",
            "can_access_admin_panel": "Доступ к админ панели"
        }
        return descriptions.get(permission, f"Разрешение: {permission}")


class PermissionDecorator:
    """Декоратор для проверки разрешений"""
    
    def __init__(self, role_manager: RoleManager, permission: str):
        self.role_manager = role_manager
        self.permission = permission
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            # Ищем user_id в аргументах
            user_id = None
            
            # Проверяем первый аргумент (обычно это message или callback_query)
            if args and hasattr(args[0], 'from_user'):
                user_id = args[0].from_user.id
            elif args and hasattr(args[0], 'message') and args[0].message:
                user_id = args[0].message.from_user.id
            
            if not user_id:
                # Если не нашли user_id, пропускаем проверку
                return await func(*args, **kwargs)
            
            # Проверяем разрешение
            if not await self.role_manager.check_permission(user_id, self.permission):
                # Отправляем сообщение об отказе в доступе
                if args and hasattr(args[0], 'answer'):
                    await args[0].answer(f"❌ У вас нет прав для доступа к этой функции.\n\nТребуется разрешение: {self.permission}")
                elif args and hasattr(args[0], 'message') and args[0].message:
                    await args[0].message.answer(f"❌ У вас нет прав для доступа к этой функции.\n\nТребуется разрешение: {self.permission}")
                return
            
            return await func(*args, **kwargs)
        
        return wrapper


def require_permission(role_manager: RoleManager, permission: str):
    """Фабрика декораторов для проверки разрешений"""
    return PermissionDecorator(role_manager, permission) 