import asyncio
import logging
from aiogram import types, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils.misc import check_permission, get_user_info, is_admin, has_admin_permissions
from bot.utils.callback_utils import _callback_cache
from bot.keyboards.inline_keyboards import (
    get_admin_panel_keyboard,
    get_auth_service_keyboard,
    get_role_management_keyboard,
    get_telegram_channels_menu_keyboard
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_user_action(func):
    """Декоратор для логирования действий пользователей"""
    async def wrapper(*args, **kwargs):
        try:
            # Получаем информацию о пользователе из первого аргумента
            if args and hasattr(args[0], 'from_user'):
                user = args[0].from_user
                user_id = user.id
                username = user.username or "Без username"
                first_name = user.first_name or "Без имени"
                last_name = user.last_name or ""
                
                # Получаем имя функции
                func_name = func.__name__
                
                print(f"🔍 [DEBUG] Функция {func_name} вызвана пользователем:")
                print(f"   ID: {user_id}")
                print(f"   Username: @{username}")
                print(f"   Имя: {first_name} {last_name}".strip())
                
                # Если это команда, выводим её
                if hasattr(args[0], 'text') and args[0].text:
                    print(f"   Команда: {args[0].text}")
                
                # Если это callback, выводим данные
                if hasattr(args[0], 'data') and args[0].data:
                    print(f"   Callback data: {args[0].data}")
                
                print(f"   Время: {asyncio.get_event_loop().time()}")
                print("=" * 50)
            
            # Вызываем оригинальную функцию
            result = await func(*args, **kwargs)
            return result
            
        except Exception as e:
            print(f"❌ [DEBUG] Ошибка в декораторе логирования: {e}")
            # В случае ошибки всё равно вызываем функцию
            return await func(*args, **kwargs)
    
    return wrapper

async def menu_admin_callback(callback_query: types.CallbackQuery):
    """Обработчик меню админа"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = (
        "⚙️ **Админ панель**\n\n"
        "Выберите раздел:\n"
        "• 🔧 Управление микросервисом - управление auth_tg_service\n"
        "• 👥 Управление ролями - создание и редактирование ролей\n"
        "• 📊 Статистика - общая статистика системы\n"
        "• 🔍 Отладка - отладочная информация"
    )
    
    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="Markdown"
    )

async def auth_service_menu_callback(callback_query: types.CallbackQuery):
    """Обработчик главного меню микросервиса"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = (
        "🔧 **Управление микросервисом auth_tg_service**\n\n"
        "Выберите действие:\n"
        "• 📊 Статус сессий - информация о всех сессиях\n"
        "• 🔍 Проверить все сессии - проверка статуса всех сессий\n"
        "• 📋 Отладка сессий - детальная информация\n"
        "• 🔄 Распределить каналы - распределение каналов по сессиям\n"
        "• 📰 Парсинг источников - управление парсингом"
    )
    
    await callback_query.message.edit_text(
        text,
        reply_markup=get_auth_service_keyboard(),
        parse_mode="Markdown"
    )

async def auth_service_status_callback(callback_query: types.CallbackQuery):
    """Обработчик получения статуса сессий"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback_query.answer("⏳ Получаем статус...")
    
    try:
        result = auth_service_client.get_status()
        if result:
            sessions = result.get("sessions", [])
            total_accounts = result.get("total_accounts", 0)
            total_channels = result.get("total_channels", 0)
            available_slots = result.get("available_slots", 0)
            
            text = (
                f"📊 **Статус сессий**\n\n"
                f"• Всего аккаунтов: {total_accounts}\n"
                f"• Всего каналов: {total_channels}\n"
                f"• Доступных слотов: {available_slots}\n\n"
                f"**Сессии:**\n"
            )
            
            for session in sessions[:10]:  # Показываем первые 10
                phone = session.get("phone_number", "N/A")
                channels_count = len(session.get("channels", []))
                status = session.get("status", "unknown")
                text += f"• {phone}: {channels_count} каналов ({status})\n"
            
            if len(sessions) > 10:
                text += f"\n... и еще {len(sessions) - 10} сессий"
        else:
            text = "❌ Ошибка при получении статуса"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_session_management_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_session_management_keyboard()
        )

async def auth_service_check_all_callback(callback_query: types.CallbackQuery):
    """Обработчик проверки всех сессий"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback_query.answer("⏳ Проверяем все сессии...")
    
    try:
        result = auth_service_client.check_all_sessions_status()
        if result:
            task_id = result.get("task_id", "N/A")
            text = (
                f"✅ **Проверка сессий запущена**\n\n"
                f"Task ID: `{task_id}`\n\n"
                f"Проверка выполняется в фоновом режиме.\n"
                f"Результаты будут отправлены в чат."
            )
        else:
            text = "❌ Ошибка при запуске проверки"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_session_management_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_session_management_keyboard()
        )

async def auth_service_debug_callback(callback_query: types.CallbackQuery):
    """Обработчик отладочной информации"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback_query.answer("⏳ Получаем отладочную информацию...")
    
    try:
        result = auth_service_client.debug_sessions()
        if result:
            sessions = result.get("sessions", [])
            total_sessions = result.get("total_sessions", 0)
            
            text = (
                f"📋 **Отладочная информация**\n\n"
                f"Всего сессий в БД: {total_sessions}\n\n"
                f"**Детали сессий:**\n"
            )
            
            for i, session in enumerate(sessions[:5]):  # Показываем первые 5
                phone = session.get("phone_number", "N/A")
                session_id = session.get("session_id", "N/A")
                created_at = session.get("created_at", "N/A")
                text += f"{i+1}. {phone}\n   ID: {session_id}\n   Создана: {created_at}\n\n"
            
            if len(sessions) > 5:
                text += f"... и еще {len(sessions) - 5} сессий"
        else:
            text = "❌ Ошибка при получении отладочной информации"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_session_management_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_session_management_keyboard()
        )

async def auth_service_distribute_callback(callback_query: types.CallbackQuery):
    """Обработчик распределения каналов"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback_query.answer("⏳ Распределяем каналы...")
    
    try:
        result = auth_service_client.distribute_channels_from_db()
        if result:
            task_id = result.get("task_id", "N/A")
            text = (
                f"🔄 **Распределение каналов запущено**\n\n"
                f"Task ID: `{task_id}`\n\n"
                f"Распределение выполняется в фоновом режиме.\n"
                f"Результаты будут отправлены в чат."
            )
        else:
            text = "❌ Ошибка при запуске распределения"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_auth_service_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_auth_service_keyboard()
        )

async def auth_service_parsing_callback(callback_query: types.CallbackQuery):
    """Обработчик меню парсинга"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = (
        "📰 **Парсинг источников**\n\n"
        "Выберите тип парсинга:\n"
        "• 🚀 Парсинг всех источников - RSS + Telegram\n"
        "• 📡 Парсинг RSS - только RSS источники\n"
        "• 📱 Парсинг Telegram - только Telegram каналы\n"
        "• 📊 Статистика парсинга - текущая статистика"
    )
    
    await callback_query.message.edit_text(
        text,
        reply_markup=get_parsing_menu_keyboard(),
        parse_mode="Markdown"
    )

async def auth_service_parse_all_callback(callback_query: types.CallbackQuery):
    """Обработчик парсинга всех источников"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback_query.answer("⏳ Запускаем парсинг всех источников...")
    
    try:
        result = auth_service_client.parse_all_sources(limit=100)
        if result:
            task_id = result.get("task_id", "N/A")
            text = (
                f"🚀 **Парсинг всех источников запущен**\n\n"
                f"Task ID: `{task_id}`\n\n"
                f"Парсинг выполняется в фоновом режиме.\n"
                f"Результаты будут отправлены в чат."
            )
        else:
            text = "❌ Ошибка при запуске парсинга"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_parsing_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_parsing_menu_keyboard()
        )

async def auth_service_parse_rss_callback(callback_query: types.CallbackQuery):
    """Обработчик парсинга RSS источников"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback_query.answer("⏳ Запускаем парсинг RSS...")
    
    try:
        result = auth_service_client.parse_rss_sources(limit=50)
        if result:
            task_id = result.get("task_id", "N/A")
            text = (
                f"📡 **Парсинг RSS источников запущен**\n\n"
                f"Task ID: `{task_id}`\n\n"
                f"Парсинг выполняется в фоновом режиме.\n"
                f"Результаты будут отправлены в чат."
            )
        else:
            text = "❌ Ошибка при запуске парсинга RSS"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_parsing_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_parsing_menu_keyboard()
        )

async def auth_service_parse_telegram_callback(callback_query: types.CallbackQuery):
    """Обработчик парсинга Telegram источников"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback_query.answer("⏳ Запускаем парсинг Telegram...")
    
    try:
        result = auth_service_client.parse_telegram_sources(limit=50)
        if result:
            task_id = result.get("task_id", "N/A")
            text = (
                f"📱 **Парсинг Telegram источников запущен**\n\n"
                f"Task ID: `{task_id}`\n\n"
                f"Парсинг выполняется в фоновом режиме.\n"
                f"Результаты будут отправлены в чат."
            )
        else:
            text = "❌ Ошибка при запуске парсинга Telegram"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_parsing_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_parsing_menu_keyboard()
        )

async def auth_service_parsing_status_callback(callback_query: types.CallbackQuery):
    """Обработчик получения статистики парсинга"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    await callback_query.answer("⏳ Получаем статистику...")
    
    try:
        result = auth_service_client.get_parsing_status()
        if result:
            total_sources = result.get("total_sources", 0)
            rss_sources = result.get("rss_sources", 0)
            telegram_sources = result.get("telegram_sources", 0)
            active_sessions = result.get("active_sessions", 0)
            total_parsed_records = result.get("total_parsed_records", 0)
            rss_parsed_records = result.get("rss_parsed_records", 0)
            telegram_parsed_records = result.get("telegram_parsed_records", 0)
            
            text = (
                f"📊 **Статистика парсинга**\n\n"
                f"**Источники:**\n"
                f"• Всего источников: {total_sources}\n"
                f"• RSS источников: {rss_sources}\n"
                f"• Telegram источников: {telegram_sources}\n"
                f"• Активных сессий: {active_sessions}\n\n"
                f"**Спарсенные записи:**\n"
                f"• Всего записей: {total_parsed_records}\n"
                f"• RSS записей: {rss_parsed_records}\n"
                f"• Telegram записей: {telegram_parsed_records}"
            )
        else:
            text = "❌ Ошибка при получении статистики"
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_parsing_menu_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_parsing_menu_keyboard()
        )

async def cmd_roles(message: types.Message):
    """Обработчик команды /roles - список ролей"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not username:
        await message.answer("❌ У вас должен быть установлен username в Telegram для использования бота.")
        return
    
    # Проверяем, является ли пользователь администратором
    if not await has_admin_permissions(user_id, username):
        await message.answer("❌ У вас нет прав для просмотра ролей.")
        return
    
    try:
        from main import get_role_manager_async as get_role_manager
        role_manager = await get_role_manager()
        
        if not role_manager:
            await message.answer("❌ Ролевая система не инициализирована.")
            return
        
        # Получаем все роли
        roles = await role_manager.get_all_roles()
        
        if not roles:
            await message.answer("📋 Роли не найдены.")
            return
        
        # Формируем список ролей
        roles_text = "📋 Доступные роли:\n\n"
        for role in roles:
            permissions_count = sum(1 for perm, enabled in role.permissions.items() if enabled)
            roles_text += f"🔹 {role.role_name}\n"
            roles_text += f"   📝 {role.description}\n"
            roles_text += f"   🔑 Разрешений: {permissions_count}\n\n"
        
        await message.answer(roles_text)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении ролей: {str(e)}")

@log_user_action
async def cmd_users(message: types.Message):
    """Обработчик команды /users - список пользователей"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    print(f"🔍 [DEBUG] Проверка команды /users для пользователя @{username} (ID: {user_id})")
    
    if not username:
        print(f"❌ [DEBUG] У пользователя ID {user_id} нет username")
        await message.answer("❌ У вас должен быть установлен username в Telegram для использования бота.")
        return
    
    try:
        # Проверяем, является ли пользователь администратором
        print(f"🔍 [DEBUG] Проверка прав администратора для @{username}...")
        is_admin_user = await has_admin_permissions(user_id, username)
        print(f"🔍 [DEBUG] Результат проверки is_admin: {is_admin_user}")
        
        if not is_admin_user:
            print(f"❌ [DEBUG] Пользователь @{username} НЕ является администратором")
            await message.answer("❌ У вас нет прав для просмотра пользователей.")
            return
        
        print(f"✅ [DEBUG] Пользователь @{username} является администратором, показываем список пользователей")
        
        # Получаем список пользователей
        from bot.utils.misc import get_role_manager_async
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен")
            await message.answer("❌ Система авторизации недоступна.")
            return
        
        print(f"🔍 [DEBUG] Получение списка пользователей...")
        users = await role_manager.user_provider.get_all_users()
        print(f"🔍 [DEBUG] Найдено пользователей: {len(users)}")
        
        if not users:
            await message.answer("📝 Пользователи не найдены.")
            return
        
        # Формируем список пользователей
        users_text = "📋 **Список пользователей:**\n\n"
        for i, user in enumerate(users, 1):
            # Обрабатываем employee_name
            employee_name = user.employee_name
            if isinstance(employee_name, dict):
                if 'name' in employee_name:
                    employee_name = employee_name['name']
                elif 'en_name' in employee_name:
                    employee_name = employee_name['en_name']
                else:
                    employee_name = str(employee_name)
            
            users_text += f"{i}. **@{user.telegram_username or 'Без username'}**\n"
            users_text += f"   👤 Имя: {employee_name or 'Не указано'}\n"
            users_text += f"   🏢 Роль: {user.role or 'Не назначена'}\n"
            users_text += f"   📊 Статус: {'✅ Активен' if user.is_active else '❌ Неактивен'}\n"
            users_text += f"   💼 Статус сотрудника: {user.employee_status or 'Не указан'}\n\n"
        
        print(f"✅ [DEBUG] Список пользователей сформирован, отправляем ответ")
        await message.answer(users_text, parse_mode="Markdown")
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при выполнении команды /users: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

async def cmd_permissions(message: types.Message):
    """Обработчик команды /permissions - информация о разрешениях пользователя"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not username:
        await message.answer("❌ У вас должен быть установлен username в Telegram для использования бота.")
        return
    
    try:
        from main import get_role_manager_async as get_role_manager
        role_manager = await get_role_manager()
        
        if not role_manager:
            await message.answer("❌ Ролевая система не инициализирована.")
            return
        
        # Проверяем доступ пользователя
        access_granted, error_message = await role_manager.check_user_access(username)
        
        if not access_granted:
            await message.answer(error_message)
            return
        
        # Получаем информацию о пользователе
        user_info = await role_manager.get_user_info(user_id)
        
        if not user_info:
            await message.answer("❌ Вы не найдены в системе пользователей.")
            return
        
        # Получаем разрешения пользователя
        permissions = await role_manager.get_user_permissions(user_id)
        
        if not permissions:
            await message.answer("❌ У вас нет назначенных разрешений.")
            return
        
        # Формируем список разрешений
        permissions_text = f"🔑 Ваши разрешения:\n\n"
        permissions_text += f"👤 Роль: {user_info.role or 'Не назначена'}\n"
        permissions_text += f"📧 Username: @{user_info.telegram_username or 'N/A'}\n\n"
        
        enabled_permissions = [perm for perm, enabled in permissions.items() if enabled]
        disabled_permissions = [perm for perm, enabled in permissions.items() if not enabled]
        
        if enabled_permissions:
            permissions_text += "✅ Разрешенные функции:\n"
            for perm in enabled_permissions:
                description = await role_manager.get_permission_description(perm)
                permissions_text += f"   • {description}\n"
        
        if disabled_permissions:
            permissions_text += "\n❌ Недоступные функции:\n"
            for perm in disabled_permissions[:5]:  # Показываем только первые 5
                description = await role_manager.get_permission_description(perm)
                permissions_text += f"   • {description}\n"
            
            if len(disabled_permissions) > 5:
                permissions_text += f"   ... и еще {len(disabled_permissions) - 5} функций"
        
        await message.answer(permissions_text)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении разрешений: {str(e)}")

async def cmd_refresh_cache(message: types.Message):
    """Обработчик команды /refresh_cache - обновление кэша пользователей"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not username:
        await message.answer("❌ У вас должен быть установлен username в Telegram для использования бота.")
        return
    
    # Проверяем, является ли пользователь администратором
    if not await has_admin_permissions(user_id, username):
        await message.answer("❌ У вас нет прав для обновления кэша.")
        return
    
    try:
        from main import get_role_manager_async as get_role_manager
        role_manager = await get_role_manager()
        
        if not role_manager:
            await message.answer("❌ Ролевая система не инициализирована.")
            return
        
        # Обновляем кэш
        await role_manager.user_provider.refresh_cache()
        
        await message.answer("✅ Кэш пользователей успешно обновлен.")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обновлении кэша: {str(e)}")

async def role_management_callback(callback_query: types.CallbackQuery):
    """Обработчик меню управления ролями"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = (
        "👥 **Управление ролями**\n\n"
        "Выберите действие:\n"
        "• ➕ Создать роль - создание новой роли с разрешениями\n"
        "• 🔧 Редактировать - изменение существующих ролей\n"
        "• 📋 Список ролей - просмотр всех ролей\n"
        "• 👥 Пользователи - управление пользователями"
    )
    
    await callback_query.message.edit_text(
        text,
        reply_markup=get_role_management_keyboard(),
        parse_mode="Markdown"
    )

async def telegram_channels_menu_callback(callback_query: types.CallbackQuery):
    """Обработчик меню управления Telegram каналами"""
    print(f"🔍 DEBUG: telegram_channels_menu_callback вызван с callback_data = {callback_query.data}")
    
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    text = (
        "📢 **Управление Telegram каналами**\n\n"
        "Здесь вы можете управлять каналами и настраивать дайджесты:\n"
        "• 📢 Список каналов - просмотр всех добавленных каналов\n"
        "• 🔧 Управление дайджестами - настройка расписания отправки\n\n"
        "Для добавления бота в канал:\n"
        "1. Добавьте бота в нужный Telegram канал как администратора\n"
        "2. Бот автоматически сохранит информацию о канале\n"
        "3. Настройте дайджесты через админскую панель"
    )
    
    print(f"🔍 DEBUG: Отправляем сообщение с текстом: {text[:100]}...")
    
    from bot.keyboards.inline_keyboards import get_telegram_channels_menu_keyboard
    
    await callback_query.message.edit_text(
        text,
        reply_markup=get_telegram_channels_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    print(f"🔍 DEBUG: Сообщение успешно отправлено")

def register_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для админских функций"""
    dp.callback_query.register(menu_admin_callback, lambda c: c.data == "menu_admin")
    dp.callback_query.register(role_management_callback, lambda c: c.data == "role_management")
    dp.callback_query.register(telegram_channels_menu_callback, lambda c: c.data == "telegram_channels_menu")
    
    # Регистрируем обработчики из telegram_channels_handlers
    from bot.handlers.telegram_channels_handlers import register_handlers as register_telegram_handlers
    register_telegram_handlers(dp)
    
    dp.callback_query.register(auth_service_menu_callback, lambda c: c.data == "auth_service_menu")
    dp.callback_query.register(auth_service_status_callback, lambda c: c.data == "auth_service_status")
    dp.callback_query.register(auth_service_check_all_callback, lambda c: c.data == "auth_service_check_all")
    dp.callback_query.register(auth_service_debug_callback, lambda c: c.data == "auth_service_debug")
    dp.callback_query.register(auth_service_distribute_callback, lambda c: c.data == "auth_service_distribute")
    dp.callback_query.register(auth_service_parsing_callback, lambda c: c.data == "auth_service_parsing")
    dp.callback_query.register(auth_service_parse_all_callback, lambda c: c.data == "auth_service_parse_all")
    dp.callback_query.register(auth_service_parse_rss_callback, lambda c: c.data == "auth_service_parse_rss")
    dp.callback_query.register(auth_service_parse_telegram_callback, lambda c: c.data == "auth_service_parse_telegram")
    dp.callback_query.register(auth_service_parsing_status_callback, lambda c: c.data == "auth_service_parsing_status") 

    # Добавляем новые команды для ролевой системы
    dp.message.register(cmd_roles, Command("roles"))
    dp.message.register(cmd_users, Command("users"))
    dp.message.register(cmd_permissions, Command("permissions"))
    dp.message.register(cmd_refresh_cache, Command("refresh_cache")) 