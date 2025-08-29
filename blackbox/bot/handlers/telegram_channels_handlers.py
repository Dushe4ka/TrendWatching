from aiogram import Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from bot.states.states import TelegramChannelStates
from bot.utils.misc import has_admin_permissions, check_permission
from bot.utils.callback_utils import parse_short_callback, _callback_cache
from bot.keyboards.inline_keyboards import (
    get_telegram_channels_menu_keyboard,
    get_telegram_channels_list_keyboard,
    get_telegram_channel_info_keyboard,
    get_digest_category_keyboard,
    get_digest_time_input_keyboard,
    get_digest_success_keyboard,
    get_digest_error_keyboard,
    get_digest_list_keyboard,
    get_digest_info_keyboard,
    get_confirm_delete_digest_keyboard,
    get_digest_edit_category_keyboard
)
from telegram_channels_service import telegram_channels_service
from database import get_categories
from bot.utils.misc import category_to_callback
from logger_config import setup_logger
import re
from bot.apscheduler_digest import add_digest_job, remove_digest_job, update_digest_job, get_digest_jobs, init_digest_jobs_from_db, start_scheduler

# Настраиваем логгер
logger = setup_logger("telegram_channels_handlers")

async def telegram_channels_list_callback(callback_query: types.CallbackQuery):
    """Обработчик списка Telegram каналов"""
    print(f"🔍 DEBUG: telegram_channels_list_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Получаем все каналы
        channels = telegram_channels_service.get_all_channels()
        
        print(f"🔍 DEBUG: Найдено каналов: {len(channels) if channels else 0}")
        
        if not channels:
            text = (
                "📢 <b>Telegram каналы</b>\n\n"
                "Каналы не найдены.\n\n"
                "Для добавления канала:\n"
                "1. Добавьте бота в нужный канал как администратора\n"
                "2. Бот автоматически сохранит информацию о канале"
            )
            
            await callback_query.message.edit_text(
                text,
                reply_markup=get_telegram_channels_menu_keyboard(),
                parse_mode="HTML"
            )
            return
        
        # Преобразуем в формат для клавиатуры
        channels_data = []
        for channel in channels:
            channels_data.append({
                "id": channel.id,
                "title": channel.title,
                "username": channel.username
            })
        
        text = (
            f"📢 <b>Telegram каналы</b> ({len(channels)})\n\n"
            "Выберите канал для управления дайджестами:"
        )
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_telegram_channels_list_keyboard(channels_data),
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в telegram_channels_list_callback: {str(e)}")
        await callback_query.message.edit_text(
            f"❌ Ошибка при получении списка каналов: {str(e)}",
            reply_markup=get_telegram_channels_menu_keyboard(),
            parse_mode="HTML"
        )

async def telegram_channel_info_callback(callback_query: types.CallbackQuery):
    """Обработчик информации о Telegram канале"""
    print(f"🔍 DEBUG: telegram_channel_info_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        
        # Проверяем, является ли это простым callback_data
        if callback_data == "telegram_channels_list":
            await telegram_channels_list_callback(callback_query)
            return
        
        # Пытаемся разобрать как короткий callback
        try:
            action, data = parse_short_callback(callback_data)
        except ValueError:
            print(f"🔍 DEBUG: Не удалось разобрать callback_data: {callback_data}")
            await callback_query.answer("❌ Ошибка: неверный формат callback")
            return
            
        print(f"🔍 DEBUG: action = {action}, data = {data}")
        
        if action == "channel_info":
            channel_id = data.get("channel_id")
            
            # Получаем информацию о канале
            channel_info = telegram_channels_service.get_channel_by_id(channel_id)
            
            if not channel_info:
                await callback_query.answer("❌ Канал не найден", show_alert=True)
                return
            
            # Получаем активные дайджесты для канала
            active_digests = telegram_channels_service.get_active_digests_by_channel(channel_id)
            
            text = (
                f"📢 <b>{channel_info.channel.title}</b>\n\n"
                f"🆔 ID: <code>{channel_id}</code>\n"
                f"👤 Username: @{channel_info.channel.username or 'Нет'}\n"
                f"📊 Активных дайджестов: {len(active_digests) if active_digests else 0}\n\n"
                "Выберите действие:"
            )
            
            await callback_query.message.edit_text(
                text,
                reply_markup=get_telegram_channel_info_keyboard(channel_id),
                parse_mode="HTML"
            )
        
        elif action == "add_digest":
            # Показываем выбор категории напрямую
            channel_id = data.get("channel_id")
            
            # Получаем доступные категории
            categories = get_categories()
            
            text = (
                "📰 <b>Добавление дайджеста</b>\n\n"
                "Выберите категорию для дайджеста:"
            )
            
            await callback_query.message.edit_text(
                text,
                reply_markup=get_digest_category_keyboard(categories, channel_id),
                parse_mode="HTML"
            )
        
        elif action == "edit_digests":
            # Вызываем обработчик редактирования дайджестов
            await edit_digests_callback(callback_query)
        
        elif action == "initialize_schedule":
            # Вызываем обработчик инициализации расписания
            await initialize_schedule_callback(callback_query)
        
        elif action == "check_schedule":
            # Вызываем обработчик проверки расписания
            await check_schedule_callback(callback_query)
        
        else:
            print(f"🔍 DEBUG: Неизвестное действие: {action}")
            await callback_query.answer(f"❌ Неизвестное действие: {action}", show_alert=True)
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в telegram_channel_info_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def add_digest_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик добавления дайджеста"""
    print(f"🔍 DEBUG: add_digest_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        if action == "add_digest":
            channel_id = data.get("channel_id")
            
            # Сохраняем данные в состоянии FSM
            await state.update_data(
                channel_id=channel_id,
                user_id=callback_query.from_user.id,
                action="add_digest"
            )
            
            # Переходим в состояние выбора категории
            await state.set_state(TelegramChannelStates.waiting_for_digest_category)
            
            # Получаем доступные категории
            categories = get_categories()
        
        text = (
                "📰 <b>Добавление дайджеста</b>\n\n"
            "Выберите категорию для дайджеста:"
        )
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_digest_category_keyboard(categories, channel_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в add_digest_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def digest_category_selected_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора категории дайджеста"""
    print(f"🔍 DEBUG: digest_category_selected_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        print(f"🔍 DEBUG: action = {action}, data = {data}")
        
        if action == "digest_cat":
            category = data.get("category")
            channel_id = data.get("channel_id")
            
            print(f"🔍 DEBUG: category = {category}, channel_id = {channel_id}")
            
            # Сохраняем все необходимые данные в состоянии FSM
            await state.update_data(
                channel_id=channel_id,
                category=category,
                user_id=callback_query.from_user.id,
                action="add_digest"
            )
            
            # Переходим в состояние ввода времени
            await state.set_state(TelegramChannelStates.waiting_for_digest_time)
        
        text = (
                "⏰ <b>Введите время отправки дайджеста</b>\n\n"
                "Формат: <code>HH:MM</code> (например: 09:00)\n"
                "Время должно быть в 24-часовом формате"
            )
        
        await callback_query.message.edit_text(
            text,
                reply_markup=get_digest_time_input_keyboard(channel_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в digest_category_selected_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def process_digest_time(message: types.Message, state: FSMContext):
    """Обработчик ввода времени для дайджеста"""
    print(f"🔍 DEBUG: process_digest_time вызван с текстом: {message.text}")
    
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        time_input = message.text.strip()
        
        # Проверяем формат времени
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_input):
            await message.answer(
                "❌ Неверный формат времени!\n\n"
                "Используйте формат <code>HH:MM</code> (например: 09:00)\n"
                "Время должно быть в 24-часовом формате",
                parse_mode="HTML"
            )
            return
        
        # Получаем данные из состояния FSM
        user_data = await state.get_data()
        channel_id = user_data.get("channel_id")
        category = user_data.get("category")
        user_id = user_data.get("user_id")
        
        print(f"🔍 DEBUG: user_data = {user_data}")
        print(f"🔍 DEBUG: channel_id = {channel_id}, category = {category}, user_id = {user_id}")
        print(f"🔍 DEBUG: Типы данных - channel_id: {type(channel_id)}, category: {type(category)}, user_id: {type(user_id)}")
        
        if not all([channel_id, category, user_id]):
            missing_data = []
            if not channel_id: missing_data.append("channel_id")
            if not category: missing_data.append("category")
            if not user_id: missing_data.append("user_id")
            await message.answer(f"❌ Ошибка: неполные данные для создания дайджеста. Отсутствует: {', '.join(missing_data)}")
            await state.clear()
            return
        
        # Создаем дайджест
        digest = telegram_channels_service.create_digest(
            channel_id=channel_id,
            category=category,
            time=time_input,
            user_id=user_id
        )
        
        if digest:
            # Добавляем задачу в планировщик
            await add_digest_job(channel_id, digest["id"], category, time_input)
            
            # Очищаем состояние FSM
            await state.clear()
            
            text = (
                "✅ <b>Дайджест успешно создан!</b>\n\n"
                f"📰 Категория: {category}\n"
                f"⏰ Время: {time_input}\n"
                f"📢 Канал: {channel_id}\n\n"
                "Дайджест будет отправляться ежедневно в указанное время."
            )
            
            await message.answer(
                text,
                reply_markup=get_digest_success_keyboard(channel_id),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "❌ Ошибка при создании дайджеста",
                reply_markup=get_digest_error_keyboard(channel_id),
                parse_mode="HTML"
            )
            await state.clear()
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в process_digest_time: {str(e)}")
        await message.answer(f"❌ Ошибка при создании дайджеста: {str(e)}")
        await state.clear()

async def edit_digests_callback(callback_query: types.CallbackQuery):
    """Обработчик редактирования дайджестов"""
    print(f"🔍 DEBUG: edit_digests_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        if action == "edit_digests":
            channel_id = data.get("channel_id")
            
            # Получаем активные дайджесты для канала
            active_digests = telegram_channels_service.get_active_digests_by_channel(channel_id)
            
            if not active_digests:
                text = (
                    "📰 <b>Редактирование дайджестов</b>\n\n"
                    "У этого канала нет активных дайджестов."
                )
                
                await callback_query.message.edit_text(
                    text,
                    reply_markup=get_telegram_channel_info_keyboard(channel_id),
                    parse_mode="HTML"
                )
                return
            
            text = (
                f"📰 <b>Редактирование дайджестов</b>\n\n"
                f"Найдено дайджестов: {len(active_digests)}\n\n"
                "Выберите дайджест для редактирования:"
            )
        
        await callback_query.message.edit_text(
            text,
                reply_markup=get_digest_list_keyboard(channel_id, active_digests),
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в edit_digests_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def digest_info_callback(callback_query: types.CallbackQuery):
    """Обработчик информации о дайджесте"""
    print(f"🔍 DEBUG: digest_info_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        if action == "digest_info":
            digest_id = data.get("digest_id")
            channel_id = data.get("channel_id")
            
            # Получаем информацию о дайджесте
            digest = telegram_channels_service.get_digest_by_id(digest_id)
        
        if not digest:
            await callback_query.answer("❌ Дайджест не найден", show_alert=True)
            return
        
        text = (
            f"📰 <b>Информация о дайджесте</b>\n\n"
                f"🆔 ID: <code>{digest['id']}</code>\n"
                f"📊 Категория: {digest['category']}\n"
                f"⏰ Время: {digest['time']}\n"
                f"📢 Канал: {digest['channel_id']}\n"
                f"📅 Создан: {digest.get('created_at', 'Неизвестно')}\n"
                f"🔄 Статус: {'Активен' if digest.get('is_active', True) else 'Неактивен'}"
            )
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_digest_info_keyboard(channel_id, digest_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в digest_info_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def edit_digest_time_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик редактирования времени дайджеста"""
    print(f"🔍 DEBUG: edit_digest_time_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        print(f"🔍 DEBUG: action = {action}, data = {data}")
        
        if action == "edit_digest_time":
            channel_id = data.get("channel_id")
            digest_id = data.get("digest_id")
            
            print(f"🔍 DEBUG: channel_id = {channel_id}, digest_id = {digest_id}")
            print(f"🔍 DEBUG: Типы данных - channel_id: {type(channel_id)}, digest_id: {type(digest_id)}")
            
            if not digest_id:
                await callback_query.answer("❌ Ошибка: не найден ID дайджеста", show_alert=True)
                return
            
            # Проверяем, что digest_id не является channel_id
            if str(digest_id).startswith('-100'):
                await callback_query.answer("❌ Ошибка: неправильный ID дайджеста", show_alert=True)
                return
            
            # Сохраняем данные в состоянии FSM
            await state.update_data(
                channel_id=channel_id,
                digest_id=digest_id,
                user_id=callback_query.from_user.id,
                edit_type="time"
            )
            
            print(f"🔍 DEBUG: Данные сохранены в состоянии FSM: channel_id={channel_id}, digest_id={digest_id}")
            
            # Переходим в состояние редактирования времени
            await state.set_state(TelegramChannelStates.editing_digest_time)
        
        text = (
                "⏰ <b>Редактирование времени дайджеста</b>\n\n"
                "Введите новое время в формате <code>HH:MM</code>\n"
                "Например: 09:00"
        )
        
        await callback_query.message.edit_text(
            text,
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в edit_digest_time_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def process_digest_edit_time(message: types.Message, state: FSMContext):
    """Обработчик ввода нового времени для редактирования дайджеста"""
    print(f"🔍 DEBUG: process_digest_edit_time вызван с текстом: {message.text}")
    
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        time_input = message.text.strip()
        
        # Проверяем формат времени
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_input):
            await message.answer(
                "❌ Неверный формат времени!\n\n"
                "Используйте формат <code>HH:MM</code> (например: 09:00)\n"
                "Время должно быть в 24-часовом формате",
                parse_mode="HTML"
            )
            return
        
        # Получаем данные из состояния FSM
        user_data = await state.get_data()
        channel_id = user_data.get("channel_id")
        digest_id = user_data.get("digest_id")
        
        print(f"🔍 DEBUG: user_data = {user_data}")
        print(f"🔍 DEBUG: channel_id = {channel_id}, digest_id = {digest_id}")
        print(f"🔍 DEBUG: Типы данных - channel_id: {type(channel_id)}, digest_id: {type(digest_id)}")
        
        if not all([channel_id, digest_id]):
            missing_data = []
            if not channel_id: missing_data.append("channel_id")
            if not digest_id: missing_data.append("digest_id")
            await message.answer(f"❌ Ошибка: неполные данные для редактирования дайджеста. Отсутствует: {', '.join(missing_data)}")
            await state.clear()
            return
        
        # Проверяем, что digest_id не является channel_id
        if str(digest_id).startswith('-100'):
            await message.answer("❌ Ошибка: неправильный ID дайджеста")
            await state.clear()
            return
        
        # Обновляем время дайджеста
        success = telegram_channels_service.update_digest_time(digest_id, time_input)
        
        if success:
            # Получаем информацию о дайджесте для обновления задачи
            digest = telegram_channels_service.get_digest_by_id(digest_id)
            if digest:
                # Обновляем задачу в планировщике
                await update_digest_job(channel_id, digest_id, digest['category'], time_input)
            
            # Очищаем состояние FSM
            await state.clear()
            
            text = (
                "✅ <b>Время дайджеста обновлено!</b>\n\n"
                f"⏰ Новое время: {time_input}\n"
                f"📰 Digest ID: {digest_id}\n\n"
                "Дайджест будет отправляться в новое время."
            )
            
            await message.answer(
                text,
                reply_markup=get_telegram_channel_info_keyboard(channel_id),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "❌ Ошибка при обновлении времени дайджеста",
                reply_markup=get_telegram_channel_info_keyboard(channel_id),
                parse_mode="HTML"
            )
            await state.clear()
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в process_digest_edit_time: {str(e)}")
        await message.answer(f"❌ Ошибка при обновлении времени дайджеста: {str(e)}")
        await state.clear()

async def edit_digest_category_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик редактирования категории дайджеста"""
    print(f"🔍 DEBUG: edit_digest_category_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        print(f"🔍 DEBUG: action = {action}, data = {data}")
        
        if action == "edit_digest_category":
            channel_id = data.get("channel_id")
            digest_id = data.get("digest_id")
            
            print(f"🔍 DEBUG: channel_id = {channel_id}, digest_id = {digest_id}")
            print(f"🔍 DEBUG: Типы данных - channel_id: {type(channel_id)}, digest_id: {type(digest_id)}")
            
            if not digest_id:
                await callback_query.answer("❌ Ошибка: не найден ID дайджеста", show_alert=True)
                return
            
            # Проверяем, что digest_id не является channel_id
            if str(digest_id).startswith('-100'):
                await callback_query.answer("❌ Ошибка: неправильный ID дайджеста", show_alert=True)
                return
        
            # Получаем доступные категории
            categories = get_categories()
            
            text = (
                "📊 <b>Редактирование категории дайджеста</b>\n\n"
                "Выберите новую категорию:"
            )
            
            # Создаем специальную клавиатуру для редактирования категории
            keyboard = get_digest_edit_category_keyboard(categories, channel_id, digest_id)
            
            await callback_query.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в edit_digest_category_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def edit_digest_category_select_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора новой категории при редактировании дайджеста"""
    print(f"🔍 DEBUG: edit_digest_category_select_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        print(f"🔍 DEBUG: action = {action}, data = {data}")
        
        if action == "edit_digest_category_select":
            channel_id = data.get("channel_id")
            digest_id = data.get("digest_id")
            category = data.get("category")
            
            print(f"🔍 DEBUG: channel_id = {channel_id}, digest_id = {digest_id}, category = {category}")
            print(f"🔍 DEBUG: Типы данных - channel_id: {type(channel_id)}, digest_id: {type(digest_id)}")
            
            if not digest_id:
                await callback_query.answer("❌ Ошибка: не найден ID дайджеста", show_alert=True)
                return
            
            # Проверяем, что digest_id не является channel_id
            if str(digest_id).startswith('-100'):
                await callback_query.answer("❌ Ошибка: неправильный ID дайджеста", show_alert=True)
                return
        
            # Обновляем категорию дайджеста
            success = telegram_channels_service.update_digest_category(digest_id, category)
        
            if success:
                # Получаем информацию о дайджесте для обновления задачи
                digest = telegram_channels_service.get_digest_by_id(digest_id)
                if digest:
                    # Обновляем задачу в планировщике
                    await update_digest_job(channel_id, digest_id, category, digest['time'])
                
                await callback_query.answer(f"✅ Категория дайджеста успешно изменена на '{category}'!")
                
                # Возвращаемся к информации о дайджесте
                await digest_info_callback(callback_query)
            else:
                await callback_query.answer("❌ Ошибка при изменении категории дайджеста", show_alert=True)
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в edit_digest_category_select_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def delete_digest_callback(callback_query: types.CallbackQuery):
    """Обработчик удаления дайджеста"""
    print(f"🔍 DEBUG: delete_digest_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        if action == "delete_digest":
            channel_id = data.get("channel_id")
            digest_id = data.get("digest_id")
        
        text = (
                "🗑️ <b>Удаление дайджеста</b>\n\n"
                f"📰 Digest ID: {digest_id}\n\n"
                "Вы действительно хотите удалить этот дайджест?\n"
                "Это действие нельзя отменить."
        )
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_confirm_delete_digest_keyboard(channel_id, digest_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в delete_digest_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def confirm_delete_digest_callback(callback_query: types.CallbackQuery):
    """Обработчик подтверждения удаления дайджеста"""
    print(f"🔍 DEBUG: confirm_delete_digest_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        if action == "confirm_delete_digest":
            channel_id = data.get("channel_id")
            digest_id = data.get("digest_id")
        
                # Удаляем дайджест
        success = telegram_channels_service.delete_digest(digest_id)
        
        if success:
            # Удаляем задачу из планировщика
            await remove_digest_job(digest_id)
            
            text = (
                "✅ <b>Дайджест успешно удален!</b>\n\n"
                f"📰 Digest ID: {digest_id}\n"
                "Дайджест больше не будет отправляться."
            )
            
            await callback_query.message.edit_text(
                text,
                reply_markup=get_telegram_channel_info_keyboard(channel_id),
                parse_mode="HTML"
            )
        else:
            await callback_query.answer("❌ Ошибка при удалении дайджеста", show_alert=True)
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в confirm_delete_digest_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def test_digest_callback(callback_query: types.CallbackQuery):
    """Обработчик тестирования дайджеста"""
    print(f"🔍 DEBUG: test_digest_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        if action == "test_digest":
            channel_id = data.get("channel_id")
            digest_id = data.get("digest_id")
            
            # Получаем информацию о дайджесте
            digest = telegram_channels_service.get_digest_by_id(digest_id)
            
            if not digest:
                await callback_query.answer("❌ Дайджест не найден", show_alert=True)
                return
            
            # Отправляем тестовый дайджест
            from celery_app.tasks.digest_tasks import send_test_digest
            
            # Запускаем задачу отправки тестового дайджеста
            task = send_test_digest.delay(channel_id, digest['category'])
            
            await callback_query.answer(
                f"✅ Тестовый дайджест запущен! Task ID: {task.id}",
                show_alert=True
            )
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в test_digest_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def schedule_digests_now_callback(callback_query: types.CallbackQuery):
    """Обработчик для немедленного запуска дайджестов"""
    print(f"🔍 DEBUG: schedule_digests_now_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Парсим callback data
        callback_data = callback_query.data
        action, data = parse_short_callback(callback_data)
        
        if action == "schedule_digests_now":
            channel_id = data.get("channel_id")
            
            # Отправляем сообщение о начале планирования
            await callback_query.message.edit_text(
                "🔄 Запуск дайджестов...\n\n"
                "Пожалуйста, подождите..."
            )
            
        # Запускаем задачу планирования дайджестов
        from celery_app.tasks.digest_tasks import schedule_daily_digests
        
        task = schedule_daily_digests.delay()
        
        await callback_query.answer(
            f"✅ Планирование дайджестов запущено! Task ID: {task.id}",
            show_alert=True
        )
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def initialize_schedule_callback(callback: types.CallbackQuery):
    """Обработчик для инициализации расписания дайджестов"""
    try:
        # Парсим callback data
        callback_data = callback.data
        action, data = parse_short_callback(callback_data)
        
        if action == "initialize_schedule":
            channel_id = data.get("channel_id")
            
            # Отправляем сообщение о начале инициализации
            await callback.message.edit_text(
                "🔄 Инициализация расписания дайджестов...\n\n"
                "Пожалуйста, подождите..."
            )
            
            # Запускаем задачу инициализации
            active_digests = telegram_channels_service.get_active_digests()
            await init_digest_jobs_from_db(active_digests)
            
            await callback.message.edit_text(
                "✅ <b>Расписание дайджестов инициализировано!</b>\n\n"
                "Все активные дайджесты добавлены в планировщик.\n"
                "Дайджесты будут отправляться ежедневно в указанное время.",
                reply_markup=get_telegram_channel_info_keyboard(channel_id),
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"Ошибка в initialize_schedule_callback: {str(e)}")
        await callback.answer("❌ Произошла ошибка при инициализации расписания")

async def check_schedule_callback(callback: types.CallbackQuery):
    """Обработчик для проверки статуса расписания дайджестов"""
    try:
        # Парсим callback data
        callback_data = callback.data
        action, data = parse_short_callback(callback_data)
        
        if action == "check_schedule":
            channel_id = data.get("channel_id")
            
            # Отправляем сообщение о проверке расписания
            await callback.message.edit_text(
                "🔄 Проверка статуса расписания дайджестов...\n\n"
                "Пожалуйста, подождите..."
            )
            
            # Запускаем задачу проверки расписания
            jobs = await get_digest_jobs()
            if not jobs:
                await callback.message.edit_text(
                    "В расписании нет задач на отправку дайджестов.",
                    reply_markup=get_telegram_channel_info_keyboard(channel_id),
                    parse_mode="HTML"
                )
                return
            text = f"🗓️ В расписании {len(jobs)} задач:\n"
            for idx, job in enumerate(jobs, 1):
                args = job.args if hasattr(job, 'args') else job.kwargs.get('args', [])
                channel_id = args[0] if len(args) > 0 else '—'
                digest_id = args[1] if len(args) > 1 else '—'
                category = args[2] if len(args) > 2 else '—'
                time_str = args[3] if len(args) > 3 else '?'
                # Получаем название канала (если возможно)
                channel_title = str(channel_id)
                try:
                    channel_info = telegram_channels_service.get_channel_by_id(channel_id)
                    if channel_info and hasattr(channel_info, 'channel'):
                        channel_title = channel_info.channel.title
                except Exception:
                    pass
                text += f"\n{idx}. 📰 Категория: {category}\n   Канал: {channel_title}\n   Время: {time_str}\n   Digest ID: {digest_id}\n"
            await callback.message.edit_text(
                text,
                reply_markup=get_telegram_channel_info_keyboard(channel_id),
                parse_mode="HTML"
            )
        
    except Exception as e:
        logger.error(f"Ошибка в check_schedule_callback: {str(e)}")
        await callback.answer("❌ Произошла ошибка при проверке статуса расписания")

def register_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для управления Telegram каналами"""
    
    # Регистрируем callback обработчики
    dp.callback_query.register(telegram_channels_list_callback, lambda c: c.data == "telegram_channels_list")
    
    # Регистрируем обработчики для конкретных действий
    # telegram_channel_info_callback обрабатывает основные действия с каналами
    dp.callback_query.register(telegram_channel_info_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] in [
        'channel_info', 'add_digest', 'edit_digests', 'initialize_schedule', 'check_schedule'
    ])
    
    # Остальные обработчики регистрируем для их конкретных действий
    dp.callback_query.register(add_digest_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'add_digest')
    dp.callback_query.register(digest_category_selected_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'digest_cat')
    dp.callback_query.register(edit_digests_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'edit_digests')
    dp.callback_query.register(digest_info_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'digest_info')
    dp.callback_query.register(edit_digest_time_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'edit_digest_time')
    dp.callback_query.register(edit_digest_category_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'edit_digest_category')
    dp.callback_query.register(edit_digest_category_select_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'edit_digest_category_select')
    dp.callback_query.register(delete_digest_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'delete_digest')
    dp.callback_query.register(confirm_delete_digest_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'confirm_delete_digest')
    dp.callback_query.register(test_digest_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'test_digest')
    dp.callback_query.register(schedule_digests_now_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'schedule_digests_now')
    dp.callback_query.register(initialize_schedule_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'initialize_schedule')
    dp.callback_query.register(check_schedule_callback, lambda c: c.data in _callback_cache and _callback_cache[c.data]['action'] == 'check_schedule')
    
    # Регистрируем обработчики сообщений с состояниями FSM
    dp.message.register(process_digest_time, TelegramChannelStates.waiting_for_digest_time)
    dp.message.register(process_digest_edit_time, TelegramChannelStates.editing_digest_time) 