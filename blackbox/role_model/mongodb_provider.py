from typing import Dict, List, Optional
from .base_provider import BaseRoleProvider, RolePermissions
from database import db
from logger_config import setup_logger

# Настраиваем логгер
logger = setup_logger("mongodb_provider")


class MongoDBRoleProvider(BaseRoleProvider):
    """Провайдер ролей для MongoDB"""
    
    def __init__(self):
        self.collection = db.roles
        self.logger = logger
        self._ensure_default_roles()
    
    def _ensure_default_roles(self):
        """Создает роли по умолчанию, если их нет"""
        try:
            # Проверяем, есть ли уже роли в базе
            existing_roles = list(self.collection.find({}, {"name": 1}))
            if existing_roles:
                self.logger.info(f"Роли уже существуют в базе ({len(existing_roles)} ролей)")
                return
            
            # Создаем роли по умолчанию с новыми правами
            default_roles = [
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
            
            # Вставляем роли по одной, чтобы избежать дублирования
            for role in default_roles:
                try:
                    self.collection.insert_one(role)
                    self.logger.info(f"Создана роль: {role['name']}")
                except Exception as e:
                    self.logger.warning(f"Роль {role['name']} уже существует: {e}")
            
            self.logger.info("Роли по умолчанию созданы")
            
        except Exception as e:
            self.logger.error(f"Ошибка при создании ролей по умолчанию: {e}")
            raise
    
    async def ensure_default_roles(self):
        """Асинхронная версия создания ролей по умолчанию"""
        try:
            # Проверяем, есть ли уже роли в базе
            count = self.collection.count_documents({})
            if count == 0:
                logger.info("Создание ролей по умолчанию...")
                self._create_default_roles()
                logger.info("Роли по умолчанию созданы успешно")
            else:
                logger.info(f"Роли уже существуют в базе ({count} ролей)")
        except Exception as e:
            logger.error(f"Ошибка при создании ролей по умолчанию: {e}")
            raise
    
    def _create_default_roles(self):
        """Создать роли по умолчанию"""
        default_roles = [
            {
                "role_name": "admin",
                "permissions": {
                    "can_use_analysis": True,
                    "can_manage_sources": True,
                    "can_receive_digest": True,
                    "can_auth_telegram": True,
                    "can_create_roles": True,
                    "can_manage_roles": True
                },
                "description": "Полный доступ ко всем функциям",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "role_name": "manager",
                "permissions": {
                    "can_use_analysis": True,
                    "can_manage_sources": True,
                    "can_receive_digest": True,
                    "can_auth_telegram": True,
                    "can_create_roles": False,
                    "can_manage_roles": False
                },
                "description": "Доступ к управлению источниками и аналитике",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "role_name": "analyst",
                "permissions": {
                    "can_use_analysis": True,
                    "can_manage_sources": False,
                    "can_receive_digest": True,
                    "can_auth_telegram": False,
                    "can_create_roles": False,
                    "can_manage_roles": False
                },
                "description": "Доступ к аналитике и дайджестам",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "role_name": "tester",
                "permissions": {
                    "can_use_analysis": True,
                    "can_manage_sources": False,
                    "can_receive_digest": False,
                    "can_auth_telegram": False,
                    "can_create_roles": False,
                    "can_manage_roles": False
                },
                "description": "Ограниченный доступ для тестирования",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        for role_data in default_roles:
            try:
                self.collection.insert_one(role_data)
                logger.info(f"Создана роль по умолчанию: {role_data['role_name']}")
            except Exception as e:
                logger.error(f"Ошибка при создании роли {role_data['role_name']}: {e}")
    
    async def get_role_permissions(self, role_name: str) -> Optional[RolePermissions]:
        """Получить разрешения для роли"""
        try:
            # Очищаем имя роли от лишних символов
            clean_role_name = role_name.strip()
            if not clean_role_name:
                return None
            
            # Пробуем найти по новому формату (поле 'name')
            role_doc = self.collection.find_one({"name": clean_role_name})
            if not role_doc:
                # Если не найдено, пробуем по старому формату (поле 'role_name')
                role_doc = self.collection.find_one({"role_name": clean_role_name})
                if not role_doc:
                    return None
            
            # Определяем имя роли из найденного документа
            role_name_field = role_doc.get("name") or role_doc.get("role_name")
            
            return RolePermissions(
                role_name=role_name_field,
                permissions=role_doc["permissions"],
                description=role_doc.get("description", "")
            )
        except Exception as e:
            logger.error(f"Ошибка при получении роли {role_name}: {e}")
            return None
    
    async def get_all_roles(self) -> List[RolePermissions]:
        """Получить все роли"""
        try:
            roles = []
            # Получаем все роли и сортируем по имени
            for role_doc in self.collection.find({}).sort("name", 1):
                # Определяем имя роли из найденного документа
                role_name_field = role_doc.get("name") or role_doc.get("role_name")
                
                role = RolePermissions(
                    role_name=role_name_field,
                    permissions=role_doc["permissions"],
                    description=role_doc.get("description", "")
                )
                roles.append(role)
            return roles
        except Exception as e:
            logger.error(f"Ошибка при получении всех ролей: {e}")
            return []
    
    async def create_role(self, role_name: str, permissions: Dict[str, bool], description: str = "") -> bool:
        """Создать новую роль"""
        try:
            # Очищаем имя роли от лишних символов
            clean_role_name = role_name.strip()
            if not clean_role_name:
                logger.error("Имя роли не может быть пустым")
                return False
            
            # Проверяем, не существует ли уже роль с таким именем (по новому формату)
            if self.collection.count_documents({"name": clean_role_name}) > 0:
                logger.warning(f"Роль {clean_role_name} уже существует")
                return False
            
            from datetime import datetime
            role_doc = {
                "name": clean_role_name,
                "permissions": permissions,
                "description": description,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.collection.insert_one(role_doc)
            logger.info(f"Роль {clean_role_name} создана успешно")
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании роли {role_name}: {e}")
            return False
    
    async def update_role(self, role_name: str, permissions: Dict[str, bool], description: str = "") -> bool:
        """Обновить роль"""
        try:
            # Очищаем имя роли от лишних символов
            clean_role_name = role_name.strip()
            if not clean_role_name:
                logger.error("Имя роли не может быть пустым")
                return False
            
            from datetime import datetime
            update_data = {
                "permissions": permissions,
                "description": description,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Пробуем обновить по новому формату (поле 'name')
            result = self.collection.update_one(
                {"name": clean_role_name},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Роль {clean_role_name} обновлена успешно")
                return True
            
            # Если не найдено, пробуем по старому формату (поле 'role_name')
            result = self.collection.update_one(
                {"role_name": clean_role_name},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Роль {clean_role_name} обновлена успешно")
                return True
            else:
                logger.warning(f"Роль {clean_role_name} не найдена для обновления")
                return False
        except Exception as e:
            logger.error(f"Ошибка при обновлении роли {role_name}: {e}")
            return False
    
    async def delete_role(self, role_name: str) -> bool:
        """Удалить роль"""
        try:
            # Очищаем имя роли от лишних символов
            clean_role_name = role_name.strip()
            if not clean_role_name:
                logger.error("Имя роли не может быть пустым")
                return False
            
            # Пробуем удалить по новому формату (поле 'name')
            result = self.collection.delete_one({"name": clean_role_name})
            if result.deleted_count > 0:
                logger.info(f"Роль {clean_role_name} удалена успешно")
                return True
            
            # Если не найдено, пробуем по старому формату (поле 'role_name')
            result = self.collection.delete_one({"role_name": clean_role_name})
            if result.deleted_count > 0:
                logger.info(f"Роль {clean_role_name} удалена успешно")
                return True
            else:
                logger.warning(f"Роль {clean_role_name} не найдена для удаления")
                return False
        except Exception as e:
            logger.error(f"Ошибка при удалении роли {role_name}: {e}")
            return False
    
    async def role_exists(self, role_name: str) -> bool:
        """Проверить существование роли"""
        try:
            # Очищаем имя роли от лишних символов
            clean_role_name = role_name.strip()
            if not clean_role_name:
                return False
            
            # Пробуем найти по новому формату (поле 'name')
            count = self.collection.count_documents({"name": clean_role_name})
            if count > 0:
                return True
            
            # Если не найдено, пробуем по старому формату (поле 'role_name')
            count = self.collection.count_documents({"role_name": clean_role_name})
            return count > 0
        except Exception as e:
            logger.error(f"Ошибка при проверке существования роли {role_name}: {e}")
            return False
    
    async def get_role_info(self, role_name: str) -> Optional[Dict]:
        """Получить полную информацию о роли"""
        try:
            # Очищаем имя роли от лишних символов
            clean_role_name = role_name.strip()
            if not clean_role_name:
                return None
            
            # Пробуем найти по новому формату (поле 'name')
            role_doc = self.collection.find_one({"name": clean_role_name})
            if not role_doc:
                # Если не найдено, пробуем по старому формату (поле 'role_name')
                role_doc = self.collection.find_one({"role_name": clean_role_name})
            
            if role_doc:
                # Убираем _id из документа
                role_doc.pop("_id", None)
                return role_doc
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении информации о роли {role_name}: {e}")
            return None
    
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