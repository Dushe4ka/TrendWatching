import asyncio
from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from ..keyboards.inline_keyboards import get_main_menu_keyboard
from ..utils.misc import get_role_manager_async


async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start с новой логикой проверки доступа"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    print(f"🚀 [DEBUG] Команда /start от пользователя ID: {user_id}")
    print(f"📱 [DEBUG] Username из Telegram: '{username}'")
    print(f"👤 [DEBUG] Имя пользователя: '{message.from_user.first_name}'")
    print(f"📝 [DEBUG] Полное имя: '{message.from_user.full_name}'")
    
    if not username:
        print(f"❌ [DEBUG] У пользователя ID {user_id} НЕТ username в Telegram")
        await message.answer("❌ У вас должен быть установлен username в Telegram для использования бота.")
        return
    
    print(f"✅ [DEBUG] У пользователя ID {user_id} ЕСТЬ username: @{username}")
    
    try:
        # Получаем ролевой менеджер
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
            await message.answer("❌ Система авторизации недоступна. Попробуйте позже.")
            return
        
        print(f"🔍 [DEBUG] Проверка доступа для @{username}...")
        
        # Проверяем доступ пользователя через username
        access_granted, error_message = await role_manager.check_user_access(username)
        
        if not access_granted:
            print(f"❌ [DEBUG] Доступ НЕ разрешен для @{username}: {error_message}")
            await message.answer(error_message)
            return
        
        print(f"✅ [DEBUG] Доступ разрешен для @{username}, показываем главное меню")
        
        # Если доступ разрешен, показываем главное меню
        await show_main_menu(message, state)
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при обработке команды /start для @{username}: {e}")
        await message.answer("❌ Произошла ошибка при проверке доступа. Попробуйте позже.")


async def cmd_main_menu(message: types.Message, state: FSMContext):
    """Обработчик команды /main_menu с новой логикой проверки доступа"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    print(f"📋 [DEBUG] Команда /main_menu от пользователя ID: {user_id}")
    print(f"📱 [DEBUG] Username из Telegram: '{username}'")
    
    if not username:
        print(f"❌ [DEBUG] У пользователя ID {user_id} НЕТ username в Telegram")
        await message.answer("❌ У вас должен быть установлен username в Telegram для использования бота.")
        return
    
    print(f"✅ [DEBUG] У пользователя ID {user_id} ЕСТЬ username: @{username}")
    
    try:
        # Получаем ролевой менеджер
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
            await message.answer("❌ Система авторизации недоступна. Попробуйте позже.")
            return
        
        print(f"🔍 [DEBUG] Проверка доступа для @{username}...")
        
        # Проверяем доступ пользователя через username
        access_granted, error_message = await role_manager.check_user_access(username)
        
        if not access_granted:
            print(f"❌ [DEBUG] Доступ НЕ разрешен для @{username}: {error_message}")
            await message.answer(error_message)
            return
        
        print(f"✅ [DEBUG] Доступ разрешен для @{username}, показываем главное меню")
        
        # Если доступ разрешен, показываем главное меню
        await show_main_menu(message, state)
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при обработке команды /main_menu для @{username}: {e}")
        await message.answer("❌ Произошла ошибка при проверке доступа. Попробуйте позже.")


async def show_main_menu(message: types.Message, state: FSMContext):
    """Показать главное меню с проверкой прав на функции"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    print(f"📋 [DEBUG] Создание главного меню для пользователя ID: {user_id}, username: @{username}")
    
    try:
        # Получаем ролевой менеджер
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
            await message.answer("❌ Система авторизации недоступна.")
            return
        
        # Получаем информацию о пользователе
        user_info = await role_manager.get_user_by_username(username)
        if not user_info:
            print(f"❌ [DEBUG] Информация о пользователе @{username} не найдена")
            await message.answer("❌ Информация о пользователе не найдена.")
            return
        
        print(f"🔍 [DEBUG] Информация о пользователе: {user_info}")
        
        # Получаем разрешения пользователя через username
        permissions = await role_manager.get_user_permissions_by_username(username)
        print(f"🔑 [DEBUG] Разрешения пользователя @{username}: {permissions}")
        
        # Формируем приветственное сообщение
        welcome_text = f"👋 Привет, @{username}!\n\n"
        welcome_text += f"🏢 Роль: {user_info.role or 'Не назначена'}\n"
        welcome_text += f"🔑 Доступных функций: {sum(permissions.values())}\n\n"
        welcome_text += "Выберите действие:"
        
        print(f"📝 [DEBUG] Текст приветствия: {welcome_text}")
        
        # Создаем клавиатуру с проверкой прав
        keyboard = await create_main_menu_keyboard(permissions)
        print(f"⌨️ [DEBUG] Клавиатура создана с {len(keyboard.inline_keyboard)} строками")
        
        await message.answer(welcome_text, reply_markup=keyboard)
        print(f"✅ [DEBUG] Главное меню отправлено пользователю @{username}")
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при показе главного меню для @{username}: {e}")
        await message.answer("❌ Произошла ошибка при загрузке меню.")


async def create_main_menu_keyboard(permissions: dict):
    """Создать клавиатуру главного меню с проверкой прав"""
    from ..keyboards.inline_keyboards import get_main_menu_keyboard
    
    print(f"⌨️ [DEBUG] Создание клавиатуры для разрешений: {permissions}")
    
    # Получаем базовую клавиатуру
    keyboard = get_main_menu_keyboard()
    print(f"🔍 [DEBUG] Базовая клавиатура: {len(keyboard.inline_keyboard)} строк")
    
    # Проверяем права на каждую функцию и скрываем недоступные
    available_buttons = []
    
    for row_index, row in enumerate(keyboard.inline_keyboard):
        print(f"🔍 [DEBUG] Обработка строки {row_index + 1}: {len(row)} кнопок")
        new_row = []
        for button_index, button in enumerate(row):
            button_text = button.text
            print(f"  🔍 [DEBUG] Кнопка {button_index + 1}: '{button_text}'")
            
            # Проверяем права на основе текста кнопки
            if "Анализ" in button_text:
                has_permission = permissions.get("can_use_analysis", False)
                print(f"    🔍 [DEBUG] Кнопка 'Анализ' - разрешение can_use_analysis: {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
                if not has_permission:
                    print(f"    ❌ [DEBUG] Кнопка 'Анализ' скрыта - нет разрешения")
                    continue
            elif "Источники" in button_text:
                has_permission = permissions.get("can_manage_sources", False)
                print(f"    🔍 [DEBUG] Кнопка 'Источники' - разрешение can_manage_sources: {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
                if not has_permission:
                    print(f"    ❌ [DEBUG] Кнопка 'Источники' скрыта - нет разрешения")
                    continue
            elif "Дайджест" in button_text:
                has_permission = permissions.get("can_receive_digest", False)
                print(f"    🔍 [DEBUG] Кнопка 'Дайджест' - разрешение can_receive_digest: {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
                if not has_permission:
                    print(f"    ❌ [DEBUG] Кнопка 'Дайджест' скрыта - нет разрешения")
                    continue
            elif "Telegram" in button_text:
                has_permission = permissions.get("can_auth_telegram", False)
                print(f"    🔍 [DEBUG] Кнопка 'Telegram' - разрешение can_auth_telegram: {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
                if not has_permission:
                    print(f"    ❌ [DEBUG] Кнопка 'Telegram' скрыта - нет разрешения")
                    continue
            elif "Роли" in button_text:
                has_permission = permissions.get("can_create_roles", False)
                print(f"    🔍 [DEBUG] Кнопка 'Роли' - разрешение can_create_roles: {'✅ ЕСТЬ' if has_permission else '❌ НЕТ'}")
                if not has_permission:
                    print(f"    ❌ [DEBUG] Кнопка 'Роли' скрыта - нет разрешения")
                    continue
            else:
                print(f"    ⚠️ [DEBUG] Кнопка '{button_text}' - неизвестный тип, добавляется без проверки")
            
            new_row.append(button)
            print(f"    ✅ [DEBUG] Кнопка '{button_text}' добавлена в строку {row_index + 1}")
        
        if new_row:  # Добавляем строку только если в ней есть кнопки
            available_buttons.append(new_row)
            print(f"  ✅ [DEBUG] Строка {row_index + 1} добавлена с {len(new_row)} кнопками")
        else:
            print(f"  ❌ [DEBUG] Строка {row_index + 1} пропущена - нет доступных кнопок")
    
    # Создаем новую клавиатуру только с доступными кнопками
    final_keyboard = types.InlineKeyboardMarkup(inline_keyboard=available_buttons)
    print(f"✅ [DEBUG] Финальная клавиатура создана: {len(available_buttons)} строк, {sum(len(row) for row in available_buttons)} кнопок")
    
    return final_keyboard


async def main_menu_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик кнопок главного меню с проверкой прав"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    data = callback_query.data
    
    print(f"🔘 [DEBUG] Нажатие кнопки '{data}' от пользователя ID: {user_id}, username: @{username}")
    
    if not username:
        print(f"❌ [DEBUG] У пользователя ID {user_id} нет username")
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    try:
        # Получаем ролевой менеджер
        role_manager = await get_role_manager_async()
        if not role_manager:
            print(f"❌ [DEBUG] Ролевой менеджер недоступен для пользователя ID {user_id}")
            await callback_query.answer("❌ Система авторизации недоступна.", show_alert=True)
            return
        
        print(f"🔍 [DEBUG] Проверка доступа для @{username}...")
        
        # Проверяем доступ пользователя
        access_granted, error_message = await role_manager.check_user_access(username)
        
        if not access_granted:
            print(f"❌ [DEBUG] Доступ НЕ разрешен для @{username}: {error_message}")
            await callback_query.answer(error_message, show_alert=True)
            return
        
        print(f"✅ [DEBUG] Доступ разрешен для @{username}")
        
        # Проверяем права на конкретное действие
        permission_required = get_permission_for_action(data)
        if permission_required:
            print(f"🔍 [DEBUG] Проверка разрешения '{permission_required}' для действия '{data}'")
            has_permission = await role_manager.check_permission(user_id, permission_required, username)
            if not has_permission:
                print(f"❌ [DEBUG] У @{username} НЕТ разрешения '{permission_required}' для действия '{data}'")
                await callback_query.answer("❌ Ваша роль не обладает правами для этого действия, обратитесь к администратору", show_alert=True)
                return
            print(f"✅ [DEBUG] У @{username} ЕСТЬ разрешение '{permission_required}' для действия '{data}'")
        else:
            print(f"⚠️ [DEBUG] Для действия '{data}' не требуется специальное разрешение")
        
        # Если все проверки пройдены, обрабатываем действие
        print(f"🎯 [DEBUG] Обработка действия '{data}' для @{username}")
        await handle_main_menu_action(callback_query, data, state)
        
    except Exception as e:
        print(f"❌ [DEBUG] Ошибка при обработке главного меню для @{username}: {e}")
        await callback_query.answer("❌ Произошла ошибка.", show_alert=True)


def get_permission_for_action(action: str) -> str:
    """Получить требуемое разрешение для действия"""
    permission_map = {
        "analysis": "can_use_analysis",
        "sources": "can_manage_sources", 
        "digest": "can_receive_digest",
        "telegram_auth": "can_auth_telegram",
        "role_management": "can_create_roles"
    }
    
    permission = permission_map.get(action, "")
    print(f"🔍 [DEBUG] Действие '{action}' -> разрешение '{permission}'")
    
    return permission


async def handle_main_menu_action(callback_query: types.CallbackQuery, action: str, state: FSMContext):
    """Обработка действий главного меню"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    print(f"🎯 [DEBUG] Обработка действия '{action}' для пользователя @{username} (ID: {user_id})")
    
    # Здесь будет логика обработки различных действий
    # Пока просто отвечаем, что функция в разработке
    response_text = f"🔧 Функция '{action}' находится в разработке"
    print(f"📝 [DEBUG] Отправка ответа: {response_text}")
    
    await callback_query.answer(response_text, show_alert=True)
    print(f"✅ [DEBUG] Ответ отправлен пользователю @{username}")


def register_main_handlers(dp: Dispatcher):
    """Регистрация основных хендлеров"""
    dp.message.register(cmd_start, commands=["start"])
    dp.message.register(cmd_main_menu, commands=["main_menu"])
    dp.callback_query.register(main_menu_callback, lambda c: c.data in ["analysis", "sources", "digest", "telegram_auth", "role_management"]) 