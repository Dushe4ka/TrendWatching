import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import time
from .base_provider import BaseUserProvider, BaseRoleProvider, UserInfo, RolePermissions
from database import db


class LarkUserProvider(BaseUserProvider):
    """Провайдер пользователей для Lark Base"""
    
    def __init__(self, app_id: str, app_secret: str, table_app_id: str, table_id: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.table_app_id = table_app_id
        self.table_id = table_id
        self._access_token = None
        self._users_cache = {}
        self._users_by_id_cache = {}  # Кэш по user_id
        self._cache_expires = 0
        self.users_lark_collection = db.users_lark  # Коллекция для хранения пользователей из Lark
        self._sync_task = None  # Задача синхронизации
    
    async def start_periodic_sync(self):
        """Запустить периодическую синхронизацию"""
        if self._sync_task is None:
            self._sync_task = asyncio.create_task(self._periodic_sync())
    
    async def stop_periodic_sync(self):
        """Остановить периодическую синхронизацию"""
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
    
    async def _periodic_sync(self):
        """Периодическая синхронизация каждые 10 минут"""
        while True:
            try:
                await self.sync_users_from_lark()
                print(f"✅ Синхронизация с Lark Base завершена: {datetime.now()}")
            except Exception as e:
                print(f"❌ Ошибка синхронизации с Lark Base: {e}")
            
            # Ждем 10 минут
            await asyncio.sleep(600)  # 600 секунд = 10 минут
    
    async def _get_access_token(self) -> str:
        """Получить токен доступа к Lark API"""
        if self._access_token and time.time() < self._cache_expires:
            return self._access_token
        
        url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal/"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                data = await response.json()
                self._access_token = data["tenant_access_token"]
                # Кэшируем токен на 1 час
                self._cache_expires = time.time() + 3600
                return self._access_token
    
    async def _fetch_all_users(self) -> List[UserInfo]:
        """Получить всех пользователей из Lark Base"""
        access_token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        base_url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{self.table_app_id}/tables/{self.table_id}/records"
        
        all_users = []
        page_token = ""
        
        async with aiohttp.ClientSession() as session:
            while True:
                if page_token:
                    url = f"{base_url}?page_token={page_token}"
                else:
                    url = base_url
                
                async with session.get(url, headers=headers) as response:
                    data = await response.json()
                    
                    if not data.get("data", {}).get("items"):
                        break
                    
                    for record in data["data"]["items"]:
                        fields = record.get("fields", {})
                        
                        # Извлекаем имя сотрудника из поля Сотрудник
                        employee_name = ""
                        employee_email = ""
                        if fields.get("Сотрудник"):
                            employee_data = fields.get("Сотрудник")
                            if isinstance(employee_data, list) and employee_data:
                                # Если это список словарей, извлекаем имя и email
                                first_item = employee_data[0]
                                if isinstance(first_item, dict):
                                    employee_name = first_item.get('name', '') or first_item.get('en_name', '')
                                    employee_email = first_item.get('email', '')
                            elif isinstance(employee_data, dict):
                                # Если это словарь
                                employee_name = employee_data.get('name', '') or employee_data.get('en_name', '')
                                employee_email = employee_data.get('email', '')
                            else:
                                employee_name = str(employee_data)
                        
                        # Извлекаем Telegram username из поля Telegram
                        telegram_field = fields.get("Telegram", "")
                        if isinstance(telegram_field, list) and telegram_field:
                            telegram_username = telegram_field[0].get("text", "")
                        elif isinstance(telegram_field, str):
                            telegram_username = telegram_field
                        else:
                            telegram_username = ""
                        
                        # Убираем @ если есть
                        if telegram_username.startswith("@"):
                            telegram_username = telegram_username[1:]
                        
                        # Генерируем user_id из username (временное решение)
                        user_id = hash(telegram_username) % (2**31) if telegram_username else 0
                        
                        user_info = UserInfo(
                            user_id=user_id,
                            telegram_username=telegram_username,
                            role=fields.get("Роль"),
                            is_whitelisted=True,  # Все пользователи в Lark считаются whitelisted
                            is_active=True,
                            company_id=fields.get("Компания"),
                            employee_status=fields.get("Статус сотрудника"),
                            employee_name=employee_name,
                            employee_email=employee_email
                        )
                        all_users.append(user_info)
                    
                    if not data["data"].get("has_more"):
                        break
                    
                    page_token = data["data"].get("page_token", "")
        
        return all_users
    
    async def get_user_info(self, user_id: int) -> Optional[UserInfo]:
        """Получить информацию о пользователе"""
        print(f"🔍 [DEBUG] get_user_info вызвана для user_id: {user_id}")
        
        # Обновляем кэш если нужно
        await self._update_cache_if_needed()
        
        print(f"🔍 [DEBUG] Кэш обновлен. Размер кэша по user_id: {len(self._users_by_id_cache)}")
        
        # Сначала ищем в кэше по user_id
        if user_id in self._users_by_id_cache:
            user = self._users_by_id_cache[user_id]
            print(f"✅ [DEBUG] Пользователь найден в кэше по user_id {user_id}:")
            print(f"   - Username: @{user.telegram_username}")
            print(f"   - Имя: {user.employee_name}")
            print(f"   - Роль: {user.role}")
            print(f"   - Статус: {user.employee_status}")
            return user
        
        print(f"❌ [DEBUG] Пользователь с user_id {user_id} НЕ найден в кэше по user_id")
        print(f"🔍 [DEBUG] Доступные user_id в кэше: {list(self._users_by_id_cache.keys())[:10]}...")  # Показываем первые 10
        
        # Если не нашли, ищем по всем пользователям
        print(f"🔍 [DEBUG] Поиск по всем пользователям в кэше (размер: {len(self._users_cache)})")
        for username, user in self._users_cache.items():
            if user.user_id == user_id:
                print(f"✅ [DEBUG] Пользователь найден по user_id {user_id} в кэше по username:")
                print(f"   - Username: @{user.telegram_username}")
                print(f"   - Имя: {user.employee_name}")
                print(f"   - Роль: {user.role}")
                print(f"   - Статус: {user.employee_status}")
                self._users_by_id_cache[user_id] = user
                return user
        
        print(f"❌ [DEBUG] Пользователь с user_id {user_id} НЕ найден нигде")
        print(f"🔍 [DEBUG] Доступные username в кэше: {list(self._users_cache.keys())[:10]}...")  # Показываем первые 10
        
        return None
    
    async def get_user_by_username(self, username: str) -> Optional[UserInfo]:
        """Получить пользователя по username"""
        await self._update_cache_if_needed()
        
        # Убираем @ если есть
        if username.startswith("@"):
            username = username[1:]
        
        return self._users_cache.get(username)
    
    async def get_all_users(self) -> List[UserInfo]:
        """Получить всех пользователей"""
        await self._update_cache_if_needed()
        return list(self._users_cache.values())
    
    async def is_user_whitelisted(self, user_id: int) -> bool:
        """Проверить, есть ли пользователь в whitelist"""
        user_info = await self.get_user_info(user_id)
        return user_info is not None and user_info.is_whitelisted
    
    async def get_user_role(self, user_id: int) -> Optional[str]:
        """Получить роль пользователя"""
        user_info = await self.get_user_info(user_id)
        return user_info.role if user_info else None
    
    async def _update_cache_if_needed(self):
        """Обновить кэш пользователей если нужно"""
        current_time = time.time()
        if not self._users_cache or current_time > self._cache_expires:
            users = await self._fetch_all_users()
            self._users_cache = {user.telegram_username: user for user in users if user.telegram_username}
            # Очищаем кэш по user_id при обновлении
            self._users_by_id_cache = {}
            # Кэшируем на 5 минут
            self._cache_expires = current_time + 300
    
    async def refresh_cache(self):
        """Принудительно обновить кэш"""
        self._cache_expires = 0
        await self._update_cache_if_needed()
    
    async def sync_users_from_lark(self):
        """Синхронизировать пользователей из Lark Base и сохранить в MongoDB"""
        try:
            print(f"🔄 [DEBUG] Начало синхронизации пользователей из Lark Base...")
            
            users = await self._fetch_all_users()
            print(f"🔍 [DEBUG] Получено {len(users)} пользователей из Lark Base")
            
            # Очищаем коллекцию users_lark (синхронная операция)
            print(f"🧹 [DEBUG] Очистка коллекции users_lark...")
            delete_result = self.users_lark_collection.delete_many({})
            print(f"✅ [DEBUG] Удалено {delete_result.deleted_count} документов из коллекции users_lark")
            
            # Сохраняем пользователей в MongoDB
            saved_count = 0
            for user in users:
                if user.telegram_username:  # Сохраняем только пользователей с username
                    user_doc = {
                        "username": user.telegram_username,
                        "employee_name": user.employee_name or "",
                        "role": user.role or "Не назначена",
                        "status": "✅ Активен" if user.is_active else "❌ Неактивен",
                        "employee_status": user.employee_status or "Не указан",
                        "synced_at": datetime.now().isoformat()
                    }
                    print(f"💾 [DEBUG] Сохранение пользователя: @{user.telegram_username} - {user.employee_name} - {user.role}")
                    
                    # Используем синхронный insert_one для совместимости
                    result = self.users_lark_collection.insert_one(user_doc)
                    saved_count += 1
                    print(f"✅ [DEBUG] Пользователь @{user.telegram_username} сохранен с ID: {result.inserted_id}")
                else:
                    print(f"⚠️ [DEBUG] Пропуск пользователя без username: {user.employee_name}")
            
            print(f"💾 [DEBUG] Всего сохранено пользователей в MongoDB: {saved_count}")
            
            # Обновляем кэш
            self._users_cache = {user.telegram_username: user for user in users if user.telegram_username}
            self._users_by_id_cache = {user.user_id: user for user in users}
            self._cache_expires = time.time() + 300  # 5 минут
            
            print(f"🔄 [DEBUG] Кэш обновлен: {len(self._users_cache)} пользователей по username, {len(self._users_by_id_cache)} по user_id")
            print(f"✅ [DEBUG] Синхронизация завершена успешно")
            
            return len(users)
        except Exception as e:
            print(f"❌ [DEBUG] Ошибка при синхронизации пользователей из Lark: {e}")
            return 0
    
    async def get_user_by_username_from_lark(self, username: str) -> Optional[Dict]:
        """Получить пользователя из коллекции users_lark по username"""
        try:
            print(f"🔍 [DEBUG] Поиск пользователя в коллекции users_lark по username: '{username}'")
            
            # Убираем @ если есть
            clean_username = username.lstrip('@')
            print(f"🔍 [DEBUG] Очищенный username для поиска: '{clean_username}'")
            
            # Используем синхронный find_one для совместимости
            user_doc = self.users_lark_collection.find_one({"username": clean_username})
            
            if user_doc:
                print(f"✅ [DEBUG] Пользователь найден: {user_doc}")
            else:
                print(f"❌ [DEBUG] Пользователь с username '{clean_username}' НЕ найден в коллекции users_lark")
                print(f"🔍 [DEBUG] Содержимое коллекции users_lark:")
                try:
                    all_users = list(self.users_lark_collection.find({}))
                    print(f"   Всего пользователей в коллекции: {len(all_users)}")
                    for i, user in enumerate(all_users[:5]):  # Показываем первые 5
                        print(f"   {i+1}. username: '{user.get('username', 'N/A')}', имя: '{user.get('employee_name', 'N/A')}', роль: '{user.get('role', 'N/A')}'")
                    if len(all_users) > 5:
                        print(f"   ... и еще {len(all_users) - 5} пользователей")
                except Exception as e:
                    print(f"   ❌ Ошибка при получении списка пользователей: {e}")
            
            return user_doc
        except Exception as e:
            print(f"❌ [DEBUG] Ошибка при получении пользователя {username}: {e}")
            return None
    
    async def check_user_access(self, username: str) -> tuple[bool, str]:
        """
        Проверка доступа пользователя по новой логике
        
        Returns:
            tuple[bool, str]: (доступ разрешен, сообщение об ошибке)
        """
        try:
            print(f"🔍 [DEBUG] Начало проверки доступа для пользователя: @{username}")
            
            # Убираем @ если есть
            clean_username = username.lstrip('@')
            print(f"🔍 [DEBUG] Очищенный username: {clean_username}")
            
            # 1. Проверка наличия пользователя в локальной БД
            print(f"🔍 [DEBUG] Шаг 1: Поиск пользователя в коллекции users_lark...")
            user_doc = await self.get_user_by_username_from_lark(clean_username)
            
            if not user_doc:
                print(f"❌ [DEBUG] Пользователь @{clean_username} НЕ найден в коллекции users_lark")
                return False, "❌ Вы не найдены в системе пользователей. Обратитесь к администратору для добавления."
            
            print(f"✅ [DEBUG] Пользователь @{clean_username} найден в коллекции users_lark")
            print(f"🔍 [DEBUG] Данные пользователя: {user_doc}")
            
            # 2. Проверка статуса сотрудника
            employee_status = user_doc.get("employee_status", "")
            print(f"🔍 [DEBUG] Шаг 2: Проверка статуса сотрудника: '{employee_status}'")
            print(f"🔍 [DEBUG] Ожидаемый статус: 'Работает'")
            
            if employee_status != "Работает":
                print(f"❌ [DEBUG] Статус сотрудника НЕ 'Работает': '{employee_status}'")
                return False, "❌ Ваш статус недействителен, обратитесь к администратору для изменения статуса"
            
            print(f"✅ [DEBUG] Статус сотрудника: '{employee_status}' - проверка пройдена")
            
            # 3. Проверка роли пользователя
            role = user_doc.get("role", "")
            print(f"🔍 [DEBUG] Шаг 3: Проверка роли пользователя: '{role}'")
            print(f"🔍 [DEBUG] Ожидаемая роль: НЕ 'Не назначена'")
            
            if role == "Не назначена":
                print(f"❌ [DEBUG] Роль пользователя: 'Не назначена'")
                return False, "❌ Вам не назначена роль, обратитесь к администратору для изменения роли"
            
            print(f"✅ [DEBUG] Роль пользователя: '{role}' - проверка пройдена")
            
            # 4. Проверка наличия роли в БД blackbox.roles
            print(f"🔍 [DEBUG] Шаг 4: Проверка наличия роли '{role}' в коллекции blackbox.roles...")
            from .mongodb_provider import MongoDBRoleProvider
            role_provider = MongoDBRoleProvider()
            role_exists = await role_provider.role_exists(role)
            
            if not role_exists:
                print(f"❌ [DEBUG] Роль '{role}' НЕ найдена в коллекции blackbox.roles")
                return False, "❌ Ваша роль не зарегестрирована в боте, обратитесь к администратору для регистрации роли"
            
            print(f"✅ [DEBUG] Роль '{role}' найдена в коллекции blackbox.roles")
            print(f"🎉 [DEBUG] Все проверки пройдены! Доступ разрешен для @{username}")
            
            return True, "✅ Доступ разрешен"
            
        except Exception as e:
            print(f"❌ [DEBUG] Ошибка при проверке доступа пользователя @{username}: {e}")
            return False, "❌ Ошибка проверки доступа, обратитесь к администратору"


class LarkRoleProvider(BaseRoleProvider):
    """Провайдер ролей для Lark Base (заглушка)"""
    
    def __init__(self):
        # В Lark роли определяются вручную, поэтому используем локальное хранилище
        self._roles = {}
        self._load_default_roles()
    
    def _load_default_roles(self):
        """Загрузить роли по умолчанию"""
        default_roles = {
            "admin": RolePermissions(
                role_name="admin",
                permissions={
                    "can_use_analysis": True,
                    "can_manage_sources": True,
                    "can_receive_digest": True,
                    "can_auth_telegram": True,
                    "can_create_roles": True,
                    "can_manage_roles": True
                },
                description="Полный доступ ко всем функциям"
            ),
            "manager": RolePermissions(
                role_name="manager",
                permissions={
                    "can_use_analysis": True,
                    "can_manage_sources": True,
                    "can_receive_digest": True,
                    "can_auth_telegram": True,
                    "can_create_roles": False,
                    "can_manage_roles": False
                },
                description="Доступ к управлению источниками и аналитике"
            ),
            "analyst": RolePermissions(
                role_name="analyst",
                permissions={
                    "can_use_analysis": True,
                    "can_manage_sources": False,
                    "can_receive_digest": True,
                    "can_auth_telegram": False,
                    "can_create_roles": False,
                    "can_manage_roles": False
                },
                description="Доступ к аналитике и дайджестам"
            ),
            "tester": RolePermissions(
                role_name="tester",
                permissions={
                    "can_use_analysis": True,
                    "can_manage_sources": False,
                    "can_receive_digest": False,
                    "can_auth_telegram": False,
                    "can_create_roles": False,
                    "can_manage_roles": False
                },
                description="Ограниченный доступ для тестирования"
            )
        }
        
        self._roles.update(default_roles)
    
    async def get_role_permissions(self, role_name: str) -> Optional[RolePermissions]:
        """Получить разрешения для роли"""
        return self._roles.get(role_name)
    
    async def get_all_roles(self) -> List[RolePermissions]:
        """Получить все роли"""
        return list(self._roles.values())
    
    async def create_role(self, role_name: str, permissions: Dict[str, bool], description: str = "") -> bool:
        """Создать новую роль"""
        if role_name in self._roles:
            return False
        
        self._roles[role_name] = RolePermissions(
            role_name=role_name,
            permissions=permissions,
            description=description
        )
        return True
    
    async def update_role(self, role_name: str, permissions: Dict[str, bool], description: str = "") -> bool:
        """Обновить роль"""
        if role_name not in self._roles:
            return False
        
        self._roles[role_name] = RolePermissions(
            role_name=role_name,
            permissions=permissions,
            description=description
        )
        return True
    
    async def delete_role(self, role_name: str) -> bool:
        """Удалить роль"""
        if role_name in self._roles:
            del self._roles[role_name]
            return True
        return False
    
    async def role_exists(self, role_name: str) -> bool:
        """Проверить существование роли"""
        return role_name in self._roles 