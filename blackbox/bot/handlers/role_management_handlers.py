from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils.misc import check_permission, get_user_info, has_admin_permissions, escape_markdown
from bot.keyboards.inline_keyboards import (
    get_role_management_keyboard,
    get_role_edit_keyboard,
    get_permission_keyboard,
    get_confirm_keyboard,
    get_role_creation_keyboard,
    get_role_edit_list_keyboard,
    get_main_menu_back_keyboard
)
import json


class RoleManagementStates(StatesGroup):
    """Состояния для управления ролями"""
    waiting_for_role_name = State()
    waiting_for_role_description = State()
    waiting_for_permissions = State()
    editing_role = State()
    editing_permissions = State()
    confirming_delete = State()


async def cmd_role_management(message: types.Message):
    """Обработчик команды /role_management - управление ролями"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    if not username:
        await message.answer("❌ У вас должен быть установлен username в Telegram для использования бота.")
        return
    
    # Проверяем, является ли пользователь администратором
    if not await has_admin_permissions(user_id, username):
        await message.answer("❌ У вас нет прав для управления ролями.")
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
        roles_text = "🔧 Управление ролями\n\n"
        roles_text += "📋 Доступные роли:\n"
        
        for role in roles:
            permissions_count = sum(1 for perm, enabled in role.permissions.items() if enabled)
            roles_text += f"🔹 {role.role_name}\n"
            roles_text += f"   📝 {role.description}\n"
            roles_text += f"   🔑 Разрешений: {permissions_count}\n\n"
        
        keyboard = get_role_management_keyboard()
        await message.answer(roles_text, reply_markup=keyboard)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении ролей: {str(e)}")


async def create_role_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик создания новой роли"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    print(f"[DEBUG] create_role_callback: callback_data={callback_query.data}, user_id={user_id}")
    current_state = await state.get_state()
    print(f"[DEBUG] create_role_callback: FSM state before={current_state}")
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ У вас нет прав для создания ролей.", show_alert=True)
        return
    
    # Проверяем, не является ли это созданием роли из Lark
    if callback_query.data.startswith("create_role_"):
        role_name = callback_query.data.replace("create_role_", "")
        print(f"[DEBUG] create_role_callback: Detected Lark role creation, role_name={role_name}")
        # Очищаем предыдущее состояние и устанавливаем новое
        await state.clear()
        await state.update_data(role_name=role_name)
        await state.set_state(RoleManagementStates.waiting_for_role_description)
        print(f"[DEBUG] create_role_callback: FSM state after set_state={await state.get_state()}")
        
        await callback_query.message.edit_text(
            f"🔧 Создание роли из Lark\n\n"
            f"📝 Роль: {role_name}\n\n"
            f"Введите описание для этой роли:"
        )
    else:
        print(f"[DEBUG] create_role_callback: Standard role creation flow")
        # Очищаем предыдущее состояние
        await state.clear()
        await state.set_state(RoleManagementStates.waiting_for_role_name)
        print(f"[DEBUG] create_role_callback: FSM state after set_state={await state.get_state()}")
        await callback_query.message.edit_text(
            "🔧 Создание новой роли\n\n"
            "Введите название новой роли (например: moderator):",
            reply_markup=get_role_creation_keyboard()
        )


async def role_name_handler(message: types.Message, state: FSMContext):
    """Обработчик ввода названия роли"""
    role_name = message.text.strip().lower()
    
    if not role_name or len(role_name) < 2:
        await message.answer("❌ Название роли должно содержать минимум 2 символа.")
        return
    
    # Проверяем, не существует ли уже такая роль
    try:
        from main import get_role_manager_async as get_role_manager
        role_manager = await get_role_manager()
        
        if await role_manager.role_exists(role_name):
            await message.answer(f"❌ Роль '{role_name}' уже существует.")
            await state.clear()
            return
        
        await state.update_data(role_name=role_name)
        await state.set_state(RoleManagementStates.waiting_for_role_description)
        
        await message.answer(
            f"📝 Роль: {role_name}\n\n"
            "Введите описание роли:",
            reply_markup=get_role_creation_keyboard()
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


async def role_description_handler(message: types.Message, state: FSMContext):
    """Обработчик ввода описания роли"""
    description = message.text.strip()
    
    if not description:
        await message.answer("❌ Описание роли не может быть пустым.")
        return
    
    # Получаем данные из состояния
    state_data = await state.get_data()
    role_name = state_data.get("role_name")
    
    if not role_name:
        await message.answer("❌ Ошибка: название роли не найдено. Начните создание заново.")
        await state.clear()
        return
    
    await state.update_data(description=description)
    
    # Получаем доступные разрешения
    try:
        from main import get_role_manager_async as get_role_manager
        role_manager = await get_role_manager()
        available_permissions = await role_manager.get_available_permissions()
        
        # Создаем клавиатуру для выбора разрешений
        keyboard = get_permission_keyboard(available_permissions, {})
        
        await state.set_state(RoleManagementStates.waiting_for_permissions)
        await message.answer(
            f"🔧 Настройка разрешений для роли\n\n"
            f"📝 Роль: {role_name}\n"
            f"📄 Описание: {description}\n\n"
            f"Выберите разрешения для этой роли:",
            reply_markup=keyboard
        )
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


async def permission_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора разрешений"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ У вас нет прав для создания ролей.", show_alert=True)
        return
    
    if data == "save_permissions":
        # Сохраняем роль
        state_data = await state.get_data()
        role_name = state_data.get("role_name")
        description = state_data.get("description")
        permissions = state_data.get("permissions", {})
        
        # Отладочная информация
        print(f"DEBUG: state_data = {state_data}")
        print(f"DEBUG: role_name = {role_name}")
        print(f"DEBUG: description = {description}")
        print(f"DEBUG: permissions = {permissions}")
        
        # Проверяем, что у нас есть все необходимые данные
        if not role_name:
            await callback_query.message.edit_text(
                "❌ Ошибка: название роли не найдено. Начните создание заново.",
                reply_markup=get_main_menu_back_keyboard()
            )
            await state.clear()
            return
        
        if not description:
            await callback_query.message.edit_text(
                "❌ Ошибка: описание роли не найдено. Начните создание заново.",
                reply_markup=get_main_menu_back_keyboard()
            )
            await state.clear()
            return
        
        try:
            from main import get_role_manager_async as get_role_manager
            role_manager = await get_role_manager()
            
            # Проверяем, существует ли уже такая роль
            if await role_manager.role_exists(role_name):
                # Если роль существует, обновляем её
                success = await role_manager.update_role(role_name, permissions, description)
                action_text = "обновлена"
            else:
                # Если роли нет, создаем новую
                success = await role_manager.create_role(role_name, permissions, description)
                action_text = "создана"
            
            if success:
                await callback_query.message.edit_text(
                    f"✅ Роль '{escape_markdown(role_name)}' {action_text} успешно!\n\n"
                    f"📝 Описание: {escape_markdown(description)}\n"
                    f"🔑 Разрешений: {sum(permissions.values())}",
                    reply_markup=get_main_menu_back_keyboard()
                )
            else:
                await callback_query.message.edit_text(
                    f"❌ Ошибка при {action_text} роли '{escape_markdown(role_name)}'.",
                    reply_markup=get_main_menu_back_keyboard()
                )
            
            await state.clear()
            
        except Exception as e:
            await callback_query.message.edit_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=get_main_menu_back_keyboard()
            )
            await state.clear()
            
    elif data == "back_to_permissions_edit":
        # Возвращаемся к редактированию роли
        state_data = await state.get_data()
        role_name = state_data.get("editing_role", "")
        
        if role_name:
            await callback_query.message.edit_text(
                f"🔧 Редактирование роли: {escape_markdown(role_name)}\n\nВыберите действие:",
                reply_markup=get_role_edit_keyboard(role_name)
            )
            # Сохраняем название роли в состоянии
            await state.update_data(editing_role=role_name)
        else:
            # Если название роли потерялось, возвращаемся к списку ролей
            await callback_query.message.edit_text(
                "🔧 Редактирование ролей\n\n"
                "Выберите роль для редактирования или настройки:",
                reply_markup=get_role_edit_list_keyboard()
            )
            await state.clear()
        
    elif data == "back_to_previous_step":
        # Возвращаемся на предыдущий шаг в зависимости от контекста
        state_data = await state.get_data()
        current_state = await state.get_state()
        
        if current_state == RoleManagementStates.waiting_for_permissions:
            # Если мы на этапе выбора разрешений, возвращаемся к описанию роли
            role_name = state_data.get("role_name", "")
            description = state_data.get("description", "")
            
            if role_name and description:
                # Возвращаемся к вводу описания
                await state.set_state(RoleManagementStates.waiting_for_role_description)
                await callback_query.message.edit_text(
                    f"📝 Роль: {escape_markdown(role_name)}\n\n"
                    "Введите описание роли:",
                    reply_markup=get_role_creation_keyboard()
                )
            else:
                # Возвращаемся к вводу названия роли
                await state.set_state(RoleManagementStates.waiting_for_role_name)
                await callback_query.message.edit_text(
                    "🔧 Создание новой роли\n\n"
                    "Введите название новой роли (например: moderator):",
                    reply_markup=get_role_creation_keyboard()
                )
        elif current_state == RoleManagementStates.editing_permissions:
            # Если мы редактируем разрешения, возвращаемся к редактированию роли
            role_name = state_data.get("editing_role", "")
            if role_name:
                await callback_query.message.edit_text(
                    f"🔧 Редактирование роли: {role_name}\n\nВыберите действие:",
                    reply_markup=get_role_edit_keyboard(role_name)
                )
                # Сохраняем название роли в состоянии
                await state.update_data(editing_role=role_name)
            else:
                # Если название роли потерялось, возвращаемся к списку ролей
                await callback_query.message.edit_text(
                    "🔧 Редактирование ролей\n\n"
                    "Выберите роль для редактирования или настройки:",
                    reply_markup=get_role_edit_list_keyboard()
                )
                await state.clear()
        else:
            # По умолчанию возвращаемся в меню управления ролями
            await callback_query.message.edit_text(
                "👥 **Управление ролями**\n\n"
                "Выберите действие:\n"
                "• ➕ Создать роль - создание новой роли с разрешениями\n"
                "• 🔧 Редактировать - изменение существующих ролей\n"
                "• 📋 Список ролей - просмотр всех ролей\n"
                "• 👥 Пользователи - управление пользователями",
                reply_markup=get_role_management_keyboard(),
                parse_mode="Markdown"
            )
            await state.clear()
        
    else:
        # Переключаем разрешение
        permission = data.replace("perm_", "")
        state_data = await state.get_data()
        permissions = state_data.get("permissions", {})
        
        # Переключаем состояние разрешения
        permissions[permission] = not permissions.get(permission, False)
        await state.update_data(permissions=permissions)
        
        # Обновляем клавиатуру
        try:
            from main import get_role_manager_async as get_role_manager
            role_manager = await get_role_manager()
            available_permissions = await role_manager.get_available_permissions()
            
            keyboard = get_permission_keyboard(available_permissions, permissions)
            await callback_query.message.edit_reply_markup(reply_markup=keyboard)
            
        except Exception as e:
            await callback_query.message.edit_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=get_main_menu_back_keyboard()
            )
            await state.clear()


async def edit_role_callback(callback_query: types.CallbackQuery):
    """Обработчик редактирования роли"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ У вас нет прав для редактирования ролей.", show_alert=True)
        return
    
    try:
        from main import get_role_manager_async as get_role_manager
        role_manager = await get_role_manager()
        
        if not role_manager:
            await callback_query.message.edit_text(
                "❌ Ролевая система не инициализирована.",
                reply_markup=get_role_management_keyboard()
            )
            return
        
        # Получаем все роли из системы
        system_roles = await role_manager.get_all_roles()
        system_role_names = {role.role_name for role in system_roles}
        
        # Получаем все роли из Lark
        lark_users = await role_manager.user_provider.get_all_users()
        lark_role_names = {user.role for user in lark_users if user.role}
        
        # Находим новые роли (есть в Lark, но нет в системе)
        new_roles = lark_role_names - system_role_names
        
        # Создаем клавиатуру для выбора роли
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
        
        # Сначала показываем существующие роли
        if system_roles:
            keyboard.inline_keyboard.append([
                types.InlineKeyboardButton(text="📋 Существующие роли:", callback_data="noop")
            ])
            
            for role in system_roles:
                keyboard.inline_keyboard.append([
                    types.InlineKeyboardButton(
                        text=f"🔧 {role.role_name}",
                        callback_data=f"edit_role_{role.role_name}"
                    )
                ])
        
        # Показываем новые роли из Lark
        if new_roles:
            if system_roles:
                keyboard.inline_keyboard.append([])  # Пустая строка для разделения
            
            keyboard.inline_keyboard.append([
                types.InlineKeyboardButton(text="🆕 Новые роли из Lark:", callback_data="noop")
            ])
            
            for role_name in sorted(new_roles):
                keyboard.inline_keyboard.append([
                    types.InlineKeyboardButton(
                        text=f"➕ {role_name} (настроить)",
                        callback_data=f"create_role_{role_name}"
                    )
                ])
        
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(text="⬅️ Назад", callback_data="role_management")
        ])
        
        text = "🔧 Редактирование ролей\n\n"
        if system_roles:
            text += f"📋 Существующих ролей: {len(system_roles)}\n"
        if new_roles:
            text += f"🆕 Новых ролей из Lark: {len(new_roles)}\n"
        
        text += "\nВыберите роль для редактирования или настройки:"
        
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu_back_keyboard()
        )


async def select_role_to_edit_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора роли для редактирования"""
    data = callback_query.data
    print(f"[DEBUG] select_role_to_edit_callback: callback_data={data}")
    current_state = await state.get_state()
    print(f"[DEBUG] select_role_to_edit_callback: FSM state before={current_state}")
    
    if data == "role_management":
        # Возвращаемся в меню управления ролями
        await callback_query.message.edit_text(
            "👥 **Управление ролями**\n\n"
            "Выберите действие:\n"
            "• ➕ Создать роль - создание новой роли с разрешениями\n"
            "• 🔧 Редактировать - изменение существующих ролей\n"
            "• 📋 Список ролей - просмотр всех ролей\n"
            "• 👥 Пользователи - управление пользователями",
            reply_markup=get_role_management_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    role_name = data.replace("edit_role_", "")
    print(f"[DEBUG] select_role_to_edit_callback: role_name={role_name}")
    
    try:
        from main import get_role_manager_async as get_role_manager
        role_manager = await get_role_manager()
        
        # Получаем информацию о роли
        role_info = await role_manager.role_provider.get_role_info(role_name)
        print(f"[DEBUG] select_role_to_edit_callback: role_info={role_info}")
        
        if not role_info:
            await callback_query.message.edit_text(
                f"❌ Роль '{escape_markdown(role_name)}' не найдена.",
                reply_markup=get_main_menu_back_keyboard()
            )
            return
        
        await state.update_data(editing_role=role_name)
        print(f"[DEBUG] select_role_to_edit_callback: FSM state after update_data={await state.get_state()}")
        
        # Показываем информацию о роли
        permissions = role_info["permissions"]
        enabled_permissions = [perm for perm, enabled in permissions.items() if enabled]
        
        role_text = f"🔧 Редактирование роли: {escape_markdown(role_name)}\n\n"
        role_text += f"📝 Описание: {escape_markdown(role_info['description'])}\n"
        role_text += f"🔑 Разрешений: {len(enabled_permissions)}\n\n"
        
        if enabled_permissions:
            role_text += "✅ Разрешенные функции:\n"
            for perm in enabled_permissions:
                description = await role_manager.get_permission_description(perm)
                role_text += f"   • {escape_markdown(description)}\n"
        
        keyboard = get_role_edit_keyboard(role_name)
        await callback_query.message.edit_text(role_text, reply_markup=keyboard)
        
    except Exception as e:
        print(f"[DEBUG] select_role_to_edit_callback: Exception: {e}")
        await callback_query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu_back_keyboard()
        )


async def edit_role_options_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик опций редактирования роли"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ У вас нет прав для редактирования ролей.", show_alert=True)
        return
    
    if data == "edit_permissions":
        # Переходим к редактированию разрешений
        await state.set_state(RoleManagementStates.editing_permissions)
        
        try:
            from main import get_role_manager_async as get_role_manager
            role_manager = await get_role_manager()
            
            state_data = await state.get_data()
            role_name = state_data.get("editing_role")
            
            if not role_name:
                await callback_query.message.edit_text(
                    "❌ Ошибка: название роли не найдено. Начните редактирование заново.",
                    reply_markup=get_main_menu_back_keyboard()
                )
                await state.clear()
                return
            
            # Получаем текущие разрешения роли
            role_info = await role_manager.role_provider.get_role_info(role_name)
            if not role_info:
                await callback_query.message.edit_text(
                    f"❌ Роль '{role_name}' не найдена.",
                    reply_markup=get_main_menu_back_keyboard()
                )
                await state.clear()
                return
            
            current_permissions = role_info["permissions"]
            
            # Сохраняем название роли и текущие разрешения в состоянии для последующего сохранения
            await state.update_data(
                editing_role=role_name,
                permissions=current_permissions
            )
            
            # Получаем доступные разрешения
            available_permissions = await role_manager.get_available_permissions()
            
            # Создаем клавиатуру для редактирования разрешений
            keyboard = get_permission_keyboard(available_permissions, current_permissions)
            
            await callback_query.message.edit_text(
                f"🔧 Редактирование разрешений для роли '{escape_markdown(role_name)}'\n\n"
                f"Выберите разрешения:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            await callback_query.message.edit_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=get_main_menu_back_keyboard()
            )
            await state.clear()
            
    elif data == "delete_role":
        # Переходим к подтверждению удаления
        try:
            await state.set_state(RoleManagementStates.confirming_delete)
            
            state_data = await state.get_data()
            role_name = state_data.get("editing_role")
            
            if not role_name:
                await callback_query.message.edit_text(
                    "❌ Ошибка: название роли не найдено. Начните редактирование заново.",
                    reply_markup=get_main_menu_back_keyboard()
                )
                await state.clear()
                return
            
            keyboard = get_confirm_keyboard(f"delete_role_{role_name}")
            
            await callback_query.message.edit_text(
                f"⚠️ Удаление роли '{escape_markdown(role_name)}'\n\n"
                f"Вы уверены, что хотите удалить эту роль?\n"
                f"Это действие нельзя отменить.",
                reply_markup=keyboard
            )
        except Exception as e:
            await callback_query.message.edit_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=get_main_menu_back_keyboard()
            )
            await state.clear()
        
    elif data == "cancel_edit_role":
        # Возвращаемся в меню редактирования ролей
        await callback_query.message.edit_text(
            "🔧 Редактирование ролей\n\n"
            "Выберите роль для редактирования или настройки:",
            reply_markup=get_role_edit_list_keyboard()
        )
        await state.clear()


async def edit_permissions_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик редактирования разрешений роли"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ У вас нет прав для редактирования ролей.", show_alert=True)
        return
    
    if data == "save_permissions":
        # Сохраняем обновленные разрешения
        state_data = await state.get_data()
        role_name = state_data.get("editing_role")
        
        if not role_name:
            await callback_query.message.edit_text(
                "❌ Ошибка: название роли не найдено. Начните редактирование заново.",
                reply_markup=get_main_menu_back_keyboard()
            )
            await state.clear()
            return
        
        permissions = state_data.get("permissions", {})
        
        try:
            from main import get_role_manager_async as get_role_manager
            role_manager = await get_role_manager()
            
            # Получаем текущую информацию о роли
            role_info = await role_manager.role_provider.get_role_info(role_name)
            if not role_info:
                await callback_query.message.edit_text(
                    f"❌ Роль '{role_name}' не найдена.",
                    reply_markup=get_main_menu_back_keyboard()
                )
                await state.clear()
                return
            
            # Обновляем роль с новыми разрешениями
            success = await role_manager.update_role(role_name, permissions, role_info["description"])
            
            if success:
                await callback_query.message.edit_text(
                    f"✅ Разрешения для роли '{escape_markdown(role_name)}' обновлены успешно!\n\n"
                    f"🔑 Разрешений: {sum(permissions.values())}",
                    reply_markup=get_main_menu_back_keyboard()
                )
            else:
                await callback_query.message.edit_text(
                    f"❌ Ошибка при обновлении роли '{escape_markdown(role_name)}'.",
                    reply_markup=get_main_menu_back_keyboard()
                )
            
            await state.clear()
            
        except Exception as e:
            await callback_query.message.edit_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=get_main_menu_back_keyboard()
            )
            await state.clear()
            
    elif data == "back_to_permissions_edit":
        # Возвращаемся к редактированию роли
        state_data = await state.get_data()
        role_name = state_data.get("editing_role", "")
        
        if role_name:
            await callback_query.message.edit_text(
                f"🔧 Редактирование роли: {role_name}\n\nВыберите действие:",
                reply_markup=get_role_edit_keyboard(role_name)
            )
            # Сохраняем название роли в состоянии
            await state.update_data(editing_role=role_name)
        else:
            # Если название роли потерялось, возвращаемся к списку ролей
            await callback_query.message.edit_text(
                "🔧 Редактирование ролей\n\n"
                "Выберите роль для редактирования или настройки:",
                reply_markup=get_role_edit_list_keyboard()
            )
            await state.clear()
            
    elif data == "back_to_previous_step":
        # Возвращаемся к редактированию роли
        state_data = await state.get_data()
        role_name = state_data.get("editing_role", "")
        
        if role_name:
            await callback_query.message.edit_text(
                f"🔧 Редактирование роли: {role_name}\n\nВыберите действие:",
                reply_markup=get_role_edit_keyboard(role_name)
            )
            # Сохраняем название роли в состоянии
            await state.update_data(editing_role=role_name)
        else:
            # Если название роли потерялось, возвращаемся к списку ролей
            await callback_query.message.edit_text(
                "🔧 Редактирование ролей\n\n"
                "Выберите роль для редактирования или настройки:",
                reply_markup=get_role_edit_list_keyboard()
            )
            await state.clear()
        
    else:
        # Переключаем разрешение
        permission = data.replace("perm_", "")
        state_data = await state.get_data()
        permissions = state_data.get("permissions", {})
        
        # Переключаем состояние разрешения
        permissions[permission] = not permissions.get(permission, False)
        await state.update_data(permissions=permissions)
        
        # Обновляем клавиатуру
        try:
            from main import get_role_manager_async as get_role_manager
            role_manager = await get_role_manager()
            available_permissions = await role_manager.get_available_permissions()
            
            keyboard = get_permission_keyboard(available_permissions, permissions)
            await callback_query.message.edit_reply_markup(reply_markup=keyboard)
            
        except Exception as e:
            await callback_query.message.edit_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=get_main_menu_back_keyboard()
            )
            await state.clear()


async def delete_role_confirm_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик подтверждения удаления роли"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ У вас нет прав для удаления ролей.", show_alert=True)
        return
    
    if data.startswith("confirm_delete_role_"):
        role_name = data.replace("confirm_delete_role_", "")
        
        try:
            from main import get_role_manager_async as get_role_manager
            role_manager = await get_role_manager()
            
            success = await role_manager.delete_role(role_name)
            
            if success:
                await callback_query.message.edit_text(
                    f"✅ Роль '{escape_markdown(role_name)}' удалена успешно!",
                    reply_markup=get_main_menu_back_keyboard()
                )
            else:
                await callback_query.message.edit_text(
                    f"❌ Ошибка при удалении роли '{escape_markdown(role_name)}'.",
                    reply_markup=get_main_menu_back_keyboard()
                )
            
            await state.clear()
            
        except Exception as e:
            await callback_query.message.edit_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=get_main_menu_back_keyboard()
            )
            await state.clear()
            
    elif data == "back_to_role_edit":
        # Возвращаемся к редактированию роли
        state_data = await state.get_data()
        role_name = state_data.get("editing_role", "")
        
        if role_name:
            await callback_query.message.edit_text(
                f"🔧 Редактирование роли: {role_name}\n\nВыберите действие:",
                reply_markup=get_role_edit_keyboard(role_name)
            )
            # Сохраняем название роли в состоянии
            await state.update_data(editing_role=role_name)
        else:
            # Если название роли потерялось, возвращаемся к списку ролей
            await callback_query.message.edit_text(
                "🔧 Редактирование ролей\n\n"
                "Выберите роль для редактирования или настройки:",
                reply_markup=get_role_edit_list_keyboard()
            )
            await state.clear()


async def users_page_callback(callback_query: types.CallbackQuery):
    """Обработчик пагинации пользователей"""
    data = callback_query.data
    
    if data.startswith("users_page_"):
        try:
            page = int(data.replace("users_page_", ""))
            await list_users_callback(callback_query, page)
        except ValueError:
            await callback_query.message.edit_text(
                "❌ Ошибка пагинации",
                reply_markup=get_main_menu_back_keyboard()
            )
    elif data == "role_management":
        await callback_query.message.edit_text(
            "👥 Управление ролями\n\n"
            "Выберите действие:",
            reply_markup=get_role_management_keyboard()
        )


async def list_roles_callback(callback_query: types.CallbackQuery):
    """Обработчик списка ролей"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ У вас нет прав для просмотра ролей.", show_alert=True)
        return
    
    try:
        from main import get_role_manager_async as get_role_manager
        role_manager = await get_role_manager()
        
        if not role_manager:
            await callback_query.message.edit_text(
                "❌ Ролевая система не инициализирована.\n\n"
                "Попробуйте перезапустить бота или обратитесь к администратору.",
                reply_markup=get_role_management_keyboard()
            )
            return
        
        # Получаем все роли
        roles = await role_manager.get_all_roles()
        
        if not roles:
            await callback_query.message.edit_text(
                "📋 Роли не найдены.\n\n"
                "Создайте первую роль, нажав 'Создать роль'.",
                reply_markup=get_role_management_keyboard()
            )
            return
        
        # Формируем список ролей
        roles_text = "📋 **Список ролей**\n\n"
        
        for i, role in enumerate(roles, 1):
            permissions_count = sum(1 for perm, enabled in role.permissions.items() if enabled)
            roles_text += f"{i}. **{escape_markdown(role.role_name)}**\n"
            roles_text += f"   📝 {escape_markdown(role.description)}\n"
            roles_text += f"   🔑 Разрешений: {permissions_count}\n\n"
        
        await callback_query.message.edit_text(
            roles_text,
            reply_markup=get_role_management_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка при получении ролей: {str(e)}",
            reply_markup=get_main_menu_back_keyboard()
        )


async def list_users_callback(callback_query: types.CallbackQuery, page: int = 0):
    """Обработчик списка пользователей с пагинацией"""
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username
    
    if not username:
        await callback_query.answer("❌ У вас должен быть установлен username в Telegram.", show_alert=True)
        return
    
    if not await has_admin_permissions(user_id, username):
        await callback_query.answer("❌ У вас нет прав для просмотра пользователей.", show_alert=True)
        return
    
    try:
        from main import get_role_manager_async as get_role_manager
        role_manager = await get_role_manager()
        
        if not role_manager:
            await callback_query.message.edit_text(
                "❌ Ролевая система не инициализирована.\n\n"
                "Попробуйте перезапустить бота или обратитесь к администратору.",
                reply_markup=get_role_management_keyboard()
            )
            return
        
        # Получаем всех пользователей
        users = await role_manager.get_all_users()
        
        if not users:
            await callback_query.message.edit_text(
                "👥 Пользователи не найдены.\n\n"
                "Пользователи появятся здесь после их добавления в систему.",
                reply_markup=get_role_management_keyboard()
            )
            return
        
        # Настройки пагинации
        users_per_page = 10
        total_pages = (len(users) + users_per_page - 1) // users_per_page
        start_idx = page * users_per_page
        end_idx = min(start_idx + users_per_page, len(users))
        
        # Формируем список пользователей для текущей страницы
        users_text = f"👥 Список пользователей ({len(users)})\n"
        users_text += f"Страница {page + 1} из {total_pages}\n\n"
        
        for i, user in enumerate(users[start_idx:end_idx], start_idx + 1):
            status = "✅ Активен" if user.is_whitelisted else "❌ Неактивен"
            role = user.role or "Не назначена"
            username = user.telegram_username or "N/A"
            employee_status = getattr(user, 'employee_status', 'N/A') or 'N/A'
            
            # Обрабатываем employee_name - может быть списком словарей, словарем или строкой
            employee_name = getattr(user, 'employee_name', 'N/A')
            if isinstance(employee_name, list) and len(employee_name) > 0:
                # Если это список словарей, берем первый элемент
                first_item = employee_name[0]
                if isinstance(first_item, dict):
                    if 'name' in first_item:
                        employee_name = first_item['name']
                    elif 'en_name' in first_item:
                        employee_name = first_item['en_name']
                    else:
                        employee_name = str(first_item)
                else:
                    employee_name = str(first_item)
            elif isinstance(employee_name, dict):
                # Если это словарь, извлекаем имя
                if 'name' in employee_name:
                    employee_name = employee_name['name']
                elif 'en_name' in employee_name:
                    employee_name = employee_name['en_name']
                else:
                    employee_name = str(employee_name)
            elif not employee_name:
                employee_name = 'N/A'
            
            users_text += f"{i}. @{username}\n"
            users_text += f"   👤 Имя: {employee_name}\n"
            users_text += f"   🏢 Роль: {role}\n"
            users_text += f"   📊 Статус: {status}\n"
            users_text += f"   💼 Статус сотрудника: {employee_status}\n\n"
        
        # Создаем клавиатуру с пагинацией
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
        
        # Кнопки навигации
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"users_page_{page - 1}"
            ))
        
        if page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"users_page_{page + 1}"
            ))
        
        if nav_buttons:
            keyboard.inline_keyboard.append(nav_buttons)
        
        # Кнопка возврата
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="role_management")
        ])
        
        await callback_query.message.edit_text(
            users_text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка при получении пользователей: {str(e)}",
            reply_markup=get_main_menu_back_keyboard()
        )


def register_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для управления ролями"""
    dp.message.register(cmd_role_management, Command("role_management"))
    dp.message.register(role_name_handler, RoleManagementStates.waiting_for_role_name)
    dp.message.register(role_description_handler, RoleManagementStates.waiting_for_role_description)
    
    dp.callback_query.register(create_role_callback, lambda c: c.data == "create_role" or c.data.startswith("create_role_"))
    dp.callback_query.register(list_roles_callback, lambda c: c.data == "list_roles")
    dp.callback_query.register(edit_role_callback, lambda c: c.data == "edit_role")
    dp.callback_query.register(list_users_callback, lambda c: c.data == "list_users")
    dp.callback_query.register(users_page_callback, lambda c: c.data.startswith("users_page_") or c.data == "role_management")
    
    # Обработчики для создания ролей (состояние waiting_for_permissions)
    dp.callback_query.register(permission_callback, RoleManagementStates.waiting_for_permissions)
    
    # Обработчики для редактирования ролей
    dp.callback_query.register(select_role_to_edit_callback, lambda c: c.data.startswith("edit_role_") or c.data == "role_management")
    dp.callback_query.register(edit_role_options_callback, lambda c: c.data in ["edit_permissions", "delete_role", "cancel_edit_role"])
    
    # Обработчики для редактирования разрешений (состояние editing_permissions)
    dp.callback_query.register(edit_permissions_callback, RoleManagementStates.editing_permissions)
    
    dp.callback_query.register(delete_role_confirm_callback, lambda c: c.data.startswith("confirm_delete_role_") or c.data == "back_to_role_edit") 