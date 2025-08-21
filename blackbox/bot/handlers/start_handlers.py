from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from bot.keyboards.inline_keyboards import get_dynamic_main_menu_keyboard, get_user_main_menu_keyboard, get_admin_main_menu_keyboard
from bot.utils.misc import is_admin, check_permission, get_user_info, check_user_access

async def send_welcome_message(chat_id: int, user_info=None, user_id=None):
    """Отправляет приветственное сообщение"""
    from main import bot
    from bot.utils.misc import is_admin_from_env
    from bot.keyboards.inline_keyboards import get_dynamic_main_menu_keyboard, get_admin_main_menu_keyboard
    
    # Формируем приветственное сообщение в зависимости от роли
    if user_info and user_info.role:
        role_text = f"\n👤 Ваша роль: {user_info.role}"
    else:
        role_text = "\n⚠️ Роль не назначена. Обратитесь к администратору."
    
    welcome_text = (
        "🎉 Добро пожаловать в TrendWatching Bot!\n\n"
        "Этот бот поможет вам:\n"
        "• 📚 Управлять источниками новостей\n"
        "• 📊 Анализировать тренды и создавать дайджесты\n"
        "• 📰 Подписываться на интересующие категории\n"
        "• 🔐 Управлять авторизацией Telegram аккаунтов\n\n"
        f"{role_text}\n\n"
        "Выберите раздел в главном меню:"
    )
    
    # Сначала проверяем ADMIN_ID - администраторы получают полную клавиатуру
    if user_id and is_admin_from_env(user_id):
        print(f"🔧 [DEBUG] Пользователь ID {user_id} является администратором (ADMIN_ID) - полная клавиатура")
        keyboard = get_admin_main_menu_keyboard()
    else:
        # Если не администратор, используем динамическую клавиатуру на основе прав
        permissions = {}
        
        # Получаем права из роли
        if user_info and user_info.role:
            from role_model.mongodb_provider import MongoDBRoleProvider
            role_provider = MongoDBRoleProvider()
            role_permissions = await role_provider.get_role_permissions(user_info.role)
            if role_permissions:
                permissions = role_permissions.permissions
                print(f"👤 [DEBUG] Пользователь ID {user_id} имеет права из роли '{user_info.role}': {permissions}")
            else:
                print(f"⚠️ [DEBUG] Роль '{user_info.role}' не найдена, нет прав")
        else:
            print(f"⚠️ [DEBUG] У пользователя ID {user_id} нет роли, нет прав")
        
        # Создаем динамическую клавиатуру на основе прав
        keyboard = get_dynamic_main_menu_keyboard(permissions)
    
    await bot.send_message(chat_id, welcome_text, reply_markup=keyboard)

async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    print(f"🚀 [DEBUG] Команда /start от пользователя ID: {user_id}, username: @{username}")
    
    # Проверяем доступ пользователя
    has_access, error_message, user_role = await check_user_access(user_id, username)
    
    if not has_access:
        await message.answer(error_message)
        return
    
    # Получаем информацию о пользователе для отображения
    user_info = await get_user_info(user_id, username)
    await send_welcome_message(message.chat.id, user_info, user_id)

async def cmd_main_menu(message: types.Message):
    """Обработчик команды /main_menu"""
    from bot.utils.misc import is_admin_from_env
    from bot.keyboards.inline_keyboards import get_dynamic_main_menu_keyboard, get_admin_main_menu_keyboard
    
    user_id = message.from_user.id
    username = message.from_user.username
    
    print(f"📋 [DEBUG] Команда /main_menu от пользователя ID: {user_id}, username: @{username}")
    
    # Проверяем доступ пользователя
    has_access, error_message, user_role = await check_user_access(user_id, username)
    
    if not has_access:
        await message.answer(error_message)
        return
    
    # Получаем информацию о пользователе для определения прав
    user_info = await get_user_info(user_id, username)
    
    # Сначала проверяем ADMIN_ID - администраторы получают полную клавиатуру
    if is_admin_from_env(user_id):
        print(f"🔧 [DEBUG] Пользователь @{username} является администратором (ADMIN_ID) - полная клавиатура")
        keyboard = get_admin_main_menu_keyboard()
    else:
        # Если не администратор, используем динамическую клавиатуру на основе прав
        permissions = {}
        
        # Получаем права из роли
        if user_info and user_info.role:
            from role_model.mongodb_provider import MongoDBRoleProvider
            role_provider = MongoDBRoleProvider()
            role_permissions = await role_provider.get_role_permissions(user_info.role)
            if role_permissions:
                permissions = role_permissions.permissions
                print(f"👤 [DEBUG] Пользователь @{username} имеет права из роли '{user_info.role}': {permissions}")
            else:
                print(f"⚠️ [DEBUG] Роль '{user_info.role}' не найдена, нет прав")
        else:
            print(f"⚠️ [DEBUG] У пользователя @{username} нет роли, нет прав")
        
        # Создаем динамическую клавиатуру на основе прав
        keyboard = get_dynamic_main_menu_keyboard(permissions)
    
    await message.answer(
        "🎯 Главное меню:\nВыберите раздел:",
        reply_markup=keyboard
    )

async def main_menu_callback(callback_query: types.CallbackQuery):
    """Обработчик возврата в главное меню"""
    from bot.utils.misc import is_admin_from_env
    from bot.keyboards.inline_keyboards import get_dynamic_main_menu_keyboard, get_admin_main_menu_keyboard
    
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    print(f"🔘 [DEBUG] main_menu_callback от пользователя ID: {user_id}, username: @{username}")
    
    # Проверяем доступ пользователя
    has_access, error_message, user_role = await check_user_access(user_id, username)
    
    if not has_access:
        await callback_query.answer(error_message, show_alert=True)
        return
    
    # Получаем информацию о пользователе для определения прав
    user_info = await get_user_info(user_id, username)
    
    # Сначала проверяем ADMIN_ID - администраторы получают полную клавиатуру
    if is_admin_from_env(user_id):
        print(f"🔧 [DEBUG] Пользователь @{username} является администратором (ADMIN_ID) - полная клавиатура")
        keyboard = get_admin_main_menu_keyboard()
    else:
        # Если не администратор, используем динамическую клавиатуру на основе прав
        permissions = {}
        
        # Получаем права из роли
        if user_info and user_info.role:
            from role_model.mongodb_provider import MongoDBRoleProvider
            role_provider = MongoDBRoleProvider()
            role_permissions = await role_provider.get_role_permissions(user_info.role)
            if role_permissions:
                permissions = role_permissions.permissions
                print(f"👤 [DEBUG] Пользователь @{username} имеет права из роли '{user_info.role}': {permissions}")
            else:
                print(f"⚠️ [DEBUG] Роль '{user_info.role}' не найдена, нет прав")
        else:
            print(f"⚠️ [DEBUG] У пользователя @{username} нет роли, нет прав")
        
        # Создаем динамическую клавиатуру на основе прав
        keyboard = get_dynamic_main_menu_keyboard(permissions)
    
    await callback_query.message.edit_text(
        "🎯 Главное меню:\nВыберите раздел:",
        reply_markup=keyboard
    )

async def on_bot_added_to_group(event: types.ChatMemberUpdated):
    """Обработчик добавления бота в группу или канал"""
    print(f"🔍 DEBUG: Событие добавления бота: новый статус={event.new_chat_member.status}, старый статус={event.old_chat_member.status}")
    print(f"🔍 DEBUG: Тип чата: {event.chat.type}, название: {event.chat.title}, ID: {event.chat.id}")
    
    if event.new_chat_member.status in ("member", "administrator") and event.old_chat_member.status == "left":
        chat = event.chat
        chat_id = chat.id
        
        print(f"🔍 DEBUG: Бот добавлен в чат типа: {chat.type}")
        
        # Различаем тип чата
        if chat.type == "channel":
            # Это канал - сохраняем в БД и отправляем специальное сообщение
            print(f"🔍 DEBUG: Обрабатываем как канал")
            await handle_channel_added(chat)
        elif chat.type in ["group", "supergroup"]:
            # Это группа - отправляем обычное сообщение
            print(f"🔍 DEBUG: Обрабатываем как группу")
            await handle_group_added(chat)
        else:
            # Другие типы чатов (private) - игнорируем
            print(f"🔍 DEBUG: Игнорируем чат типа: {chat.type}")
            return
    else:
        print(f"🔍 DEBUG: Условие не выполнено: новый статус не member/admin или старый статус не left")

async def handle_channel_added(chat):
    """Обработчик добавления бота в канал"""
    try:
        print(f"🔍 DEBUG: Добавление бота в канал: {chat.title} (ID: {chat.id})")
        
        # Сохраняем информацию о канале в БД
        from telegram_channels_service import telegram_channels_service
        
        channel_data = {
            "id": chat.id,
            "title": chat.title,
            "username": chat.username,
            "type": chat.type
        }
        
        print(f"🔍 DEBUG: Сохраняем данные канала: {channel_data}")
        
        success = telegram_channels_service.add_channel(channel_data)
        
        if success:
            print(f"✅ Канал {chat.title} успешно сохранен в БД")
            
            # Отправляем сообщение в канал
            from main import bot
            text = (
                "📢 <b>Бот добавлен в канал!</b>\n\n"
                "Теперь администраторы могут настроить ежедневные дайджесты новостей:\n"
                "• Перейдите в личные сообщения с ботом\n"
                "• Выберите Админ → Telegram каналы\n"
                "• Настройте дайджесты по нужным категориям\n\n"
                "❗️ Дайджесты будут отправляться автоматически в указанное время!"
            )
            try:
                await bot.send_message(chat.id, text, parse_mode="HTML")
                print(f"✅ Сообщение отправлено в канал {chat.title}")
            except Exception as send_error:
                print(f"❌ Ошибка при отправке сообщения в канал: {str(send_error)}")
                # Пробуем отправить без форматирования
                try:
                    plain_text = (
                        "📢 Бот добавлен в канал!\n\n"
                        "Теперь администраторы могут настроить ежедневные дайджесты новостей:\n"
                        "• Перейдите в личные сообщения с ботом\n"
                        "• Выберите Админ → Telegram каналы\n"
                        "• Настройте дайджесты по нужным категориям\n\n"
                        "❗️ Дайджесты будут отправляться автоматически в указанное время!"
                    )
                    await bot.send_message(chat.id, plain_text)
                    print(f"✅ Простое сообщение отправлено в канал {chat.title}")
                except Exception as plain_error:
                    print(f"❌ Не удалось отправить даже простое сообщение: {str(plain_error)}")
        else:
            # Логируем ошибку
            print(f"❌ Ошибка при сохранении канала {chat.title} в БД")
            
    except Exception as e:
        print(f"❌ Ошибка при обработке добавления в канал: {str(e)}")
        import traceback
        traceback.print_exc()

async def handle_group_added(chat):
    """Обработчик добавления бота в группу"""
    try:
        print(f"🔍 DEBUG: Добавление бота в группу: {chat.title} (ID: {chat.id}, тип: {chat.type})")
        
        chat_id = chat.id
        text = (
            "👋 Привет! Я бот для анализа трендов в различных категориях.\n\n"
            "Теперь я в этой группе и могу присылать ежедневные новости по подписке.\n"
            "\n📊 Что я умею:\n"
            "• Формирую ежедневные и еженедельные дайджесты новостей по выбранным категориям\n"
            "• Анализирую тренды по вашему запросу\n"
            "• Помогаю отслеживать важные изменения в интересующих вас сферах\n\n"
            "Чтобы подписаться на новости для всей группы, используйте меню подписки.\n"
            "\n❗️Ежедневные новости по подписке приходят в 14:00!❗️"
        )
        # Получаем бота из диспетчера
        from main import bot
        await bot.send_message(chat_id, text)
        print(f"✅ Сообщение отправлено в группу {chat.title}")
        
    except Exception as e:
        print(f"❌ Ошибка при обработке добавления в группу: {str(e)}")
        import traceback
        traceback.print_exc()

async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    user_id = message.from_user.id
    
    # Получаем информацию о пользователе
    user_info = await get_user_info(user_id)
    
    if not user_info:
        help_text = (
            "❓ Помощь по боту:\n\n"
            "Для получения доступа к функциям бота обратитесь к администратору.\n\n"
            "Доступные команды:\n"
            "/start - Запустить бота\n"
            "/main_menu - Главное меню\n"
            "/help - Эта справка"
        )
    else:
        help_text = (
            f"❓ Помощь по боту:\n\n"
            f"👤 Ваша роль: {user_info.role or 'Не назначена'}\n"
            f"📧 Username: @{user_info.telegram_username or 'Не указан'}\n\n"
            "Доступные команды:\n"
            "/start - Запустить бота\n"
            "/main_menu - Главное меню\n"
            "/help - Эта справка\n\n"
            "Для получения дополнительной помощи обратитесь к администратору."
        )
    
    await message.answer(help_text)

def register_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для стартовых команд"""
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_main_menu, Command("main_menu"))
    dp.message.register(cmd_help, Command("help"))
    dp.callback_query.register(main_menu_callback, lambda c: c.data == "main_menu")
    dp.my_chat_member.register(on_bot_added_to_group) 