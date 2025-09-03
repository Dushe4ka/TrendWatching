# utils/misc.py
import hashlib
import os
from typing import Union, Optional, Dict
from aiogram import types
from functools import wraps
from role_model.base_provider import UserInfo

def get_subscription_id_and_type(obj: Union[types.Message, types.CallbackQuery]) -> tuple[int, str]:
    """Определяет ID и тип (user/group) для системы подписок."""
    user_id = obj.from_user.id
    chat_type = obj.chat.type if hasattr(obj, 'chat') else 'private'

    if chat_type in ["group", "supergroup"]:
        return obj.chat.id, "group"
    
    return user_id, "user"

def category_to_callback(category: str) -> str:
    """Хэширует название категории для безопасной передачи в callback_data."""
    if category == "all":
        return "all"
    
    hash_result = hashlib.md5(category.encode('utf-8')).hexdigest()[:16]
    print(f"🔍 [DEBUG] category_to_callback: {category} -> {hash_result}")
    return hash_result

def callback_to_category(callback: str, all_categories: list) -> str:
    """Восстанавливает название категории из хэша в callback_data."""
    if callback == "all":
        return "all"
    
    # Добавляем логирование для отладки
    print(f"🔍 [DEBUG] callback_to_category: callback={callback}, all_categories={all_categories}")
    
    for cat in all_categories:
        cat_hash = category_to_callback(cat)
        print(f"🔍 [DEBUG] Сравниваем: {cat} -> {cat_hash} == {callback}")
        if cat_hash == callback:
            print(f"✅ [DEBUG] Найдено совпадение: {cat}")
            return cat
    
    print(f"❌ [DEBUG] Категория не найдена для callback: {callback}")
    return None

def is_admin_from_env(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором по переменной окружения ADMIN_ID"""
    admin_ids_str = os.getenv("ADMIN_ID", "")
    
    if not admin_ids_str:
        return False
    
    # Преобразуем user_id в строку для сравнения
    user_id_str = str(user_id)
    
    # Разбиваем строку админов по запятой и убираем пробелы
    admin_ids = [admin_id.strip() for admin_id in admin_ids_str.split(",")]
    
    return user_id_str in admin_ids

async def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь администратором"""
    print(f"🔍 [DEBUG] Проверка прав администратора для пользователя ID: {user_id}")
    
    try:
        # Сначала проверяем переменную окружения ADMIN_ID
        admin_ids_str = os.getenv("ADMIN_ID")
        if admin_ids_str:
            # Разбираем строку с ID через запятую
            admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip().isdigit()]
            if user_id in admin_ids:
                print(f"✅ [DEBUG] Пользователь ID {user_id} является администратором (ADMIN_ID)")
                return True
            else:
                print(f"🔍 [DEBUG] Пользователь ID {user_id} НЕ найден в списке администраторов: {admin_ids}")
        else:
            print(f"🔍 [DEBUG] Переменная окружения ADMIN_ID не установлена")
        
        # Если пользователь не в ADMIN_ID, проверяем через ролевую систему
        # Получаем ролевой менеджер
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
            return False
        
        # Получаем информацию о пользователе
        user_info = await role_manager.get_user_info(user_id)
        if not user_info or not user_info.telegram_username:
            print(f"❌ [DEBUG] Информация о пользователе ID {user_id} не найдена или нет username")
            return False
        
        print(f"🔍 [DEBUG] Информация о пользователе: {user_info}")
        print(f"🔍 [DEBUG] Username: @{user_info.telegram_username}")
        print(f"🔍 [DEBUG] Роль: {user_info.role}")
        
        # Проверяем доступ через новую логику
        print(f"🔍 [DEBUG] Проверка доступа для @{user_info.telegram_username}...")
        access_granted, error_message = await role_manager.check_user_access(user_info.telegram_username)
        
        if not access_granted:
            print(f"❌ [DEBUG] Доступ НЕ разрешен для @{user_info.telegram_username}: {error_message}")
            return False
        
        print(f"✅ [DEBUG] Доступ разрешен для @{user_info.telegram_username}")
        
        # Проверяем, является ли роль администраторской
        is_admin_role = user_info.role and user_info.role.lower() == "admin"
        print(f"🔍 [DEBUG] Роль '{user_info.role}' является администраторской: {is_admin_role}")
        
        if is_admin_role:
            print(f"✅ [DEBUG] Пользователь @{user_info.telegram_username} является администратором")
        else:
            print(f"❌ [DEBUG] Пользователь @{user_info.telegram_username} НЕ является администратором (роль: {user_info.role})")
        
        return is_admin_role
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при проверке прав администратора для пользователя ID {user_id}: {e}")
        return False

async def is_admin_chat(chat_id: int) -> bool:
    """Проверяет, является ли чат админским"""
    # Здесь должна быть логика проверки админского чата
    # Пока возвращаем True для всех чатов
    return True

async def has_admin_permissions(user_id: int, username: str = None) -> bool:
    """Проверяет, есть ли у пользователя права на админские функции"""
    print(f"🔍 [DEBUG] Проверка админских прав для пользователя ID: {user_id}")
    
    try:
        # Сначала проверяем переменную окружения ADMIN_ID
        if is_admin_from_env(user_id):
            print(f"✅ [DEBUG] Пользователь ID {user_id} является администратором (ADMIN_ID)")
            return True
        
        # Если пользователь не в ADMIN_ID, проверяем через ролевую систему
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен")
            return False
        
        # Если у нас есть username, используем его для проверки
        if username:
            print(f"🔍 [DEBUG] Используем username для проверки админских прав: @{username}")
            
            # Получаем права пользователя по username
            user_permissions = await role_manager.get_user_permissions_by_username(username)
            if not user_permissions:
                print(f"❌ [DEBUG] Права пользователя @{username} не найдены")
                return False
            
            print(f"🔍 [DEBUG] Права пользователя @{username}: {user_permissions}")
            
            # Проверяем наличие админских прав
            admin_permissions = [
                "can_manage_telegram_auth",
                "can_access_admin_panel"
            ]
            
            has_admin_rights = any(user_permissions.get(perm, False) for perm in admin_permissions)
            
            if has_admin_rights:
                print(f"✅ [DEBUG] Пользователь имеет админские права: {user_permissions}")
            else:
                print(f"❌ [DEBUG] Пользователь не имеет админских прав: {user_permissions}")
            
            return has_admin_rights
        else:
            print(f"❌ [DEBUG] Username не предоставлен для проверки админских прав")
            return False
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при проверке админских прав: {e}")
        return False

async def check_permission(user_id: int, permission: str, username: str = None) -> bool:
    """Проверить разрешение для пользователя"""
    print(f"🔍 [DEBUG] Проверка разрешения '{permission}' для пользователя ID: {user_id}")
    if username:
        print(f"📱 [DEBUG] Username из Telegram: @{username}")
    
    try:
        # Сначала проверяем переменную окружения ADMIN_ID
        admin_ids_str = os.getenv("ADMIN_ID")
        if admin_ids_str:
            # Разбираем строку с ID через запятую
            admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip().isdigit()]
            if user_id in admin_ids:
                print(f"✅ [DEBUG] Пользователь ID {user_id} является администратором (ADMIN_ID) - все разрешения доступны")
                return True
            else:
                print(f"🔍 [DEBUG] Пользователь ID {user_id} НЕ найден в списке администраторов: {admin_ids}")
        else:
            print(f"🔍 [DEBUG] Переменная окружения ADMIN_ID не установлена")
        
        # Если у нас есть username, используем его напрямую
        if username:
            print(f"🔍 [DEBUG] Используем username для проверки разрешения: @{username}")
            
            # Получаем ролевой менеджер
            role_manager = await get_role_manager_async()
            if not role_manager:
                print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
                return False
            
            # Проверяем доступ через username
            print(f"🔍 [DEBUG] Проверка доступа через role_manager.check_user_access для @{username}...")
            access_granted, error_message = await role_manager.check_user_access(username)
            
            if not access_granted:
                print(f"❌ [DEBUG] Доступ НЕ разрешен для @{username}: {error_message}")
                return False
            
            print(f"✅ [DEBUG] Доступ разрешен для @{username}")
            
            # Проверяем конкретное разрешение
            print(f"🔍 [DEBUG] Проверка конкретного разрешения '{permission}'...")
            has_permission = await role_manager.check_permission(user_id, permission)
            
            if has_permission:
                print(f"✅ [DEBUG] У @{username} ЕСТЬ разрешение '{permission}'")
            else:
                print(f"❌ [DEBUG] У @{username} НЕТ разрешения '{permission}'")
            
            return has_permission
        
        # Если username нет, используем старую логику через ID
        print(f"🔍 [DEBUG] Username не предоставлен, используем поиск по ID")
        
        # Получаем ролевой менеджер
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
            return False
        
        # Получаем информацию о пользователе
        user_info = await role_manager.get_user_info(user_id)
        if not user_info or not user_info.telegram_username:
            print(f"❌ [DEBUG] Информация о пользователе ID {user_id} не найдена или нет username")
            return False
        
        print(f"🔍 [DEBUG] Информация о пользователе: {user_info}")
        print(f"🔍 [DEBUG] Username: @{user_info.telegram_username}")
        
        # Проверяем доступ через новую логику
        print(f"🔍 [DEBUG] Проверка доступа для @{user_info.telegram_username}...")
        access_granted, error_message = await role_manager.check_user_access(user_info.telegram_username)
        
        if not access_granted:
            print(f"❌ [DEBUG] Доступ НЕ разрешен для @{user_info.telegram_username}: {error_message}")
            return False
        
        print(f"✅ [DEBUG] Доступ разрешен для @{user_info.telegram_username}")
        
        # Проверяем конкретное разрешение
        print(f"🔍 [DEBUG] Проверка конкретного разрешения '{permission}'...")
        has_permission = await role_manager.check_permission(user_id, permission)
        
        if has_permission:
            print(f"✅ [DEBUG] У @{user_info.telegram_username} ЕСТЬ разрешение '{permission}'")
        else:
            print(f"❌ [DEBUG] У @{user_info.telegram_username} НЕТ разрешения '{permission}'")
        
        return has_permission
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при проверке разрешения '{permission}' для пользователя ID {user_id}: {e}")
        return False

async def check_user_access(user_id: int, username: str = None) -> tuple[bool, str, Optional[str]]:
    """Проверить доступ пользователя"""
    print(f"🔍 [DEBUG] Проверка доступа пользователя ID: {user_id}")
    if username:
        print(f"📱 [DEBUG] Username из Telegram: @{username}")
    
    try:
        # Сначала проверяем переменную окружения ADMIN_ID
        admin_ids_str = os.getenv("ADMIN_ID")
        if admin_ids_str:
            # Разбираем строку с ID через запятую
            admin_ids = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip().isdigit()]
            if user_id in admin_ids:
                print(f"✅ [DEBUG] Пользователь ID {user_id} является администратором (ADMIN_ID) - доступ разрешен")
                return True, "✅ Доступ разрешен (администратор)", "admin"
            else:
                print(f"🔍 [DEBUG] Пользователь ID {user_id} НЕ найден в списке администраторов: {admin_ids}")
        else:
            print(f"🔍 [DEBUG] Переменная окружения ADMIN_ID не установлена")
        
        # Если у нас есть username, используем его напрямую
        if username:
            print(f"🔍 [DEBUG] Используем username для проверки доступа: @{username}")
            
            # Получаем ролевой менеджер
            role_manager = await get_role_manager_async()
            if not role_manager:
                print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
                return False, "❌ Система авторизации недоступна.", None
            
            # Проверяем доступ через username
            print(f"🔍 [DEBUG] Проверка доступа через role_manager.check_user_access для @{username}...")
            access_granted, error_message = await role_manager.check_user_access(username)
            
            if not access_granted:
                print(f"❌ [DEBUG] Доступ НЕ разрешен для @{username}: {error_message}")
                return False, error_message, None
            
            print(f"✅ [DEBUG] Доступ разрешен для @{username}")
            return True, "", None
        
        # Если username нет, используем старую логику через ID
        print(f"🔍 [DEBUG] Username не предоставлен, используем поиск по ID")
        
        # Получаем ролевой менеджер
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
            return False, "❌ Система авторизации недоступна.", None
        
        # Получаем информацию о пользователе
        print(f"🔍 [DEBUG] Получение информации о пользователе ID {user_id}...")
        user_info = await role_manager.get_user_info(user_id)
        
        if not user_info:
            print(f"❌ [DEBUG] Информация о пользователе ID {user_id} не найдена")
            return False, "❌ Вы не найдены в системе пользователей. Обратитесь к администратору для добавления.", None
        
        if not user_info.telegram_username:
            print(f"❌ [DEBUG] У пользователя ID {user_id} нет username в системе")
            return False, "❌ Вы не найдены в системе пользователей. Обратитесь к администратору для добавления.", None
        
        print(f"✅ [DEBUG] Информация о пользователе найдена:")
        print(f"   - Username: @{user_info.telegram_username}")
        print(f"   - Имя: {user_info.employee_name}")
        print(f"   - Роль: {user_info.role}")
        print(f"   - Статус: {user_info.employee_status}")
        
        # Проверяем доступ через новую логику
        print(f"🔍 [DEBUG] Проверка доступа через role_manager.check_user_access...")
        access_granted, error_message = await role_manager.check_user_access(user_info.telegram_username)
        
        if not access_granted:
            print(f"❌ [DEBUG] Доступ НЕ разрешен для @{user_info.telegram_username}: {error_message}")
            return False, error_message, user_info.role
        
        print(f"✅ [DEBUG] Доступ разрешен для @{user_info.telegram_username}")
        return True, "", user_info.role
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при проверке доступа пользователя ID {user_id}: {e}")
        return False, f"❌ Ошибка проверки доступа: {e}", None

async def get_user_role(user_id: int) -> Optional[str]:
    """Получить роль пользователя"""
    print(f"🔍 [DEBUG] Получение роли пользователя ID: {user_id}")
    
    try:
        # Получаем ролевой менеджер
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
            return None
        
        # Получаем информацию о пользователе
        user_info = await role_manager.get_user_info(user_id)
        if not user_info:
            print(f"❌ [DEBUG] Информация о пользователе ID {user_id} не найдена")
            return None
        
        print(f"🔍 [DEBUG] Информация о пользователе: {user_info}")
        print(f"🔍 [DEBUG] Роль пользователя: {user_info.role}")
        
        # Проверяем доступ через новую логику
        if user_info.telegram_username:
            print(f"🔍 [DEBUG] Проверка доступа для @{user_info.telegram_username}...")
            access_granted, error_message = await role_manager.check_user_access(user_info.telegram_username)
            
            if not access_granted:
                print(f"❌ [DEBUG] Доступ НЕ разрешен для @{user_info.telegram_username}: {error_message}")
                return None
            
            print(f"✅ [DEBUG] Доступ разрешен для @{user_info.telegram_username}")
        else:
            print(f"❌ [DEBUG] У пользователя ID {user_id} нет username")
            return None
        
        return user_info.role
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при получении роли пользователя ID {user_id}: {e}")
        return None

async def get_user_info(user_id: int, username: str = None) -> Optional[UserInfo]:
    """Получить информацию о пользователе"""
    print(f"🔍 [DEBUG] Получение информации о пользователе ID: {user_id}")
    if username:
        print(f"📱 [DEBUG] Username из Telegram: @{username}")
    
    try:
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
            return None
        
        # Если у нас есть username, используем его напрямую
        if username:
            print(f"🔍 [DEBUG] Используем username для получения информации: @{username}")
            user_info = await role_manager.get_user_by_username(username)
            
            if user_info:
                print(f"✅ [DEBUG] Информация о пользователе найдена по username:")
                print(f"   ID: {user_info.user_id}")
                print(f"   Username: @{user_info.telegram_username}")
                print(f"   Имя: {user_info.employee_name}")
                print(f"   Роль: {user_info.role}")
                print(f"   Статус: {'Активен' if user_info.is_active else 'Неактивен'}")
                print(f"   Статус сотрудника: {user_info.employee_status}")
            else:
                print(f"❌ [DEBUG] Информация о пользователе @{username} не найдена")
            
            return user_info
        
        # Если username нет, используем старую логику через ID
        print(f"🔍 [DEBUG] Username не предоставлен, используем поиск по ID")
        print(f"🔍 [DEBUG] Ролевой менеджер получен, запрашиваем информацию о пользователе...")
        user_info = await role_manager.get_user_info(user_id)
        
        if user_info:
            print(f"✅ [DEBUG] Информация о пользователе найдена:")
            print(f"   ID: {user_info.user_id}")
            print(f"   Username: @{user_info.telegram_username}")
            print(f"   Имя: {user_info.employee_name}")
            print(f"   Роль: {user_info.role}")
            print(f"   Статус: {'Активен' if user_info.is_active else 'Неактивен'}")
            print(f"   Статус сотрудника: {user_info.employee_status}")
        else:
            print(f"❌ [DEBUG] Информация о пользователе ID {user_id} не найдена")
        
        return user_info
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при получении информации о пользователе ID {user_id}: {e}")
        return None

async def get_role_manager_async():
    """Получить ролевой менеджер асинхронно"""
    print(f"🔍 [DEBUG] Запрос ролевого менеджера...")
    
    try:
        from main import get_role_manager_async as get_manager
        role_manager = await get_manager()
        
        if role_manager:
            print(f"✅ [DEBUG] Ролевой менеджер успешно получен")
        else:
            print(f"❌ [DEBUG] Ролевой менеджер не получен (None)")
        
        return role_manager
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при получении ролевого менеджера: {e}")
        return None

async def get_user_permissions(user_id: int) -> Dict[str, bool]:
    """Получить разрешения пользователя"""
    print(f"🔍 [DEBUG] Получение разрешений пользователя ID: {user_id}")
    
    try:
        # Получаем ролевой менеджер
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
            return {}
        
        # Получаем разрешения пользователя
        print(f"🔍 [DEBUG] Запрос разрешений через role_manager.get_user_permissions...")
        permissions = await role_manager.get_user_permissions(user_id)
        
        if permissions:
            print(f"✅ [DEBUG] Разрешения получены: {permissions}")
            # Подсчитываем количество разрешений
            enabled_permissions = sum(1 for perm, enabled in permissions.items() if enabled)
            print(f"🔍 [DEBUG] Всего разрешений: {len(permissions)}, включено: {enabled_permissions}")
        else:
            print(f"❌ [DEBUG] Разрешения не получены (пустой словарь)")
        
        return permissions
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при получении разрешений пользователя ID {user_id}: {e}")
        return {}

def require_permission(permission: str):
    """Декоратор для проверки разрешения"""
    def decorator(func):
        @wraps(func)
        async def wrapper(event, *args, **kwargs):
            user_id = event.from_user.id
            username = event.from_user.username
            
            print(f"🔍 [DEBUG] require_permission: проверка разрешения '{permission}' для пользователя ID: {user_id}")
            if username:
                print(f"📱 [DEBUG] require_permission: username из Telegram: @{username}")
            
            # Проверяем разрешение
            has_permission = await check_permission(user_id, permission, username)
            
            if not has_permission:
                error_message = f"❌ Ваша роль не обладает правами для этого действия, обратитесь к администратору."
                if isinstance(event, types.CallbackQuery):
                    await event.answer(error_message, show_alert=True)
                else:
                    await event.answer(error_message)
                return
            
            # Если разрешение есть, выполняем функцию
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator

def escape_markdown(text: str) -> str:
    """Экранирует специальные Markdown символы"""
    escape_chars = r'\*_~`[]>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text
    