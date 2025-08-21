from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class UserInfo:
    """Информация о пользователе"""
    user_id: int
    telegram_username: Optional[str] = None
    role: Optional[str] = None
    is_whitelisted: bool = False
    is_active: bool = True
    company_id: Optional[str] = None
    employee_status: Optional[str] = None  # Статус сотрудника: "работает", "приостановлен", "уволен"
    employee_name: Optional[str] = None    # Имя сотрудника
    employee_email: Optional[str] = None   # Email сотрудника


@dataclass
class RolePermissions:
    """Разрешения для роли"""
    role_name: str
    permissions: Dict[str, bool]
    description: str = ""


class BaseUserProvider(ABC):
    """Базовый класс для провайдеров данных о пользователях"""
    
    @abstractmethod
    async def get_user_info(self, user_id: int) -> Optional[UserInfo]:
        """Получить информацию о пользователе"""
        pass
    
    @abstractmethod
    async def get_all_users(self) -> List[UserInfo]:
        """Получить всех пользователей"""
        pass
    
    @abstractmethod
    async def is_user_whitelisted(self, user_id: int) -> bool:
        """Проверить, есть ли пользователь в whitelist"""
        pass
    
    @abstractmethod
    async def get_user_role(self, user_id: int) -> Optional[str]:
        """Получить роль пользователя"""
        pass


class BaseRoleProvider(ABC):
    """Базовый класс для провайдеров ролей"""
    
    @abstractmethod
    async def get_role_permissions(self, role_name: str) -> Optional[RolePermissions]:
        """Получить разрешения для роли"""
        pass
    
    @abstractmethod
    async def get_all_roles(self) -> List[RolePermissions]:
        """Получить все роли"""
        pass
    
    @abstractmethod
    async def create_role(self, role_name: str, permissions: Dict[str, bool], description: str = "") -> bool:
        """Создать новую роль"""
        pass
    
    @abstractmethod
    async def update_role(self, role_name: str, permissions: Dict[str, bool], description: str = "") -> bool:
        """Обновить роль"""
        pass
    
    @abstractmethod
    async def delete_role(self, role_name: str) -> bool:
        """Удалить роль"""
        pass
    
    @abstractmethod
    async def role_exists(self, role_name: str) -> bool:
        """Проверить существование роли"""
        pass 