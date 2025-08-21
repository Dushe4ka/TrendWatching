from aiogram import Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from bot.states.states import TelegramChannelStates
from bot.utils.misc import has_admin_permissions, check_permission
from bot.utils.callback_utils import parse_short_callback
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
    get_confirm_delete_digest_keyboard
)
from telegram_channels_service import telegram_channels_service
from database import get_categories
from bot.utils.misc import category_to_callback
from logger_config import setup_logger
import re
from bot.apscheduler_digest import add_digest_job, remove_digest_job, update_digest_job, get_digest_jobs, init_digest_jobs_from_db, start_scheduler

# Настраиваем логгер
logger = setup_logger("telegram_channels_handlers")

# Отладочный хендлер для проверки всех callback данных
async def debug_callback_handler(callback_query: types.CallbackQuery):
    """Отладочный хендлер для проверки callback данных"""
    print(f"🔍 DEBUG: Получен callback: {callback_query.data}")
    print(f"🔍 DEBUG: От пользователя: {callback_query.from_user.id}")
    
    # Отвечаем на callback, чтобы убрать "часики"
    await callback_query.answer(f"DEBUG: {callback_query.data}")

# Убрал дублирующий хендлер - он теперь в admin_handlers.py

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
            
            print(f"🔍 DEBUG: Нет каналов, отправляем сообщение: {text[:100]}...")
            
            await callback_query.message.edit_text(
                text,
                reply_markup=get_telegram_channels_menu_keyboard(),
                parse_mode="HTML"
            )
            
            print(f"🔍 DEBUG: Сообщение успешно отправлено")
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
        
        print(f"🔍 DEBUG: Отправляем сообщение с текстом: {text[:100]}...")
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_telegram_channels_list_keyboard(channels_data),
            parse_mode="HTML"
        )
        
        print(f"🔍 DEBUG: Сообщение успешно отправлено")
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в telegram_channels_list_callback: {str(e)}")
        await callback_query.message.edit_text(
            f"❌ Ошибка при получении списка каналов: {str(e)}",
            reply_markup=get_telegram_channels_menu_keyboard()
        )

async def telegram_channel_info_callback(callback_query: types.CallbackQuery):
    """Обработчик информации о конкретном канале"""
    print(f"🔍 DEBUG: telegram_channel_info_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        print(f"🔍 DEBUG: action = {action}, data = {data}")
        
        # Получаем channel_id из данных (если есть)
        channel_id = data.get('channel_id') if data else None
        
        # Обрабатываем различные действия
        if action == "add_digest":
            # Вызываем функцию добавления дайджеста
            await add_digest_callback(callback_query)
            return
        elif action == "edit_digests":
            # Вызываем функцию редактирования дайджестов
            await edit_digests_callback(callback_query)
            return
        elif action == "digest_cat":
            # Вызываем функцию выбора категории для дайджеста
            await handle_digest_category_selection(callback_query)
            return
        elif action == "digest_info":
            # Вызываем функцию информации о дайджесте
            await digest_info_callback(callback_query)
            return
        elif action == "edit_digest_time":
            # Вызываем функцию изменения времени дайджеста
            await edit_digest_time_callback(callback_query, None)  # state будет None
            return
        elif action == "edit_digest_category":
            # Вызываем функцию изменения категории дайджеста
            await edit_digest_category_callback(callback_query, None)  # state будет None
            return
        elif action == "edit_digest_category_select":
            # Вызываем функцию выбора новой категории при редактировании
            await edit_digest_category_select_callback(callback_query)
            return
        elif action == "delete_digest":
            # Вызываем функцию удаления дайджеста
            await delete_digest_callback(callback_query)
            return
        elif action == "confirm_delete_digest":
            # Вызываем функцию подтверждения удаления дайджеста
            await confirm_delete_digest_callback(callback_query)
            return
        elif action == "test_digest":
            # Вызываем функцию тестирования дайджеста
            await test_digest_callback(callback_query)
            return
        elif action == "schedule_digests_now":
            await schedule_digests_now_callback(callback_query)
            return
        
        elif action == "initialize_schedule":
            await initialize_schedule_callback(callback_query)
            return
            
        elif action == "check_schedule":
            await check_schedule_callback(callback_query)
            return
            
        elif action == "back_to_channels":
            # Возвращаемся к списку каналов
            await telegram_channels_list_callback(callback_query)
            return
            
        elif action == "channel_info":
            # Показываем информацию о канале
            if action == "channel_info" and channel_id:
                # Получаем информацию о канале
                channel_info = telegram_channels_service.get_channel_by_id(channel_id)
                if not channel_info:
                    await callback_query.answer("❌ Канал не найден", show_alert=True)
                    return
                # Формируем текст с информацией о канале
                text = (
                    f"📢 <b>Канал: {channel_info.channel.title}</b>\n\n"
                )
                if channel_info.channel.username:
                    text += f"Username: @{channel_info.channel.username}\n"
                text += f"ID: <code>{channel_info.channel.id}</code>\n"
                text += f"Тип: {channel_info.channel.type}\n"
                text += f"Дайджестов: {len(channel_info.digests)}\n\n"
                if channel_info.digests:
                    text += "<b>Активные дайджесты:</b>\n"
                    for digest in channel_info.digests:
                        status = "✅" if digest.is_active else "⏸️"
                        text += f"{status} {digest.category} - {digest.time}\n"
                else:
                    text += "Дайджесты не настроены"
                # Отправляем сообщение с информацией о канале
                await callback_query.message.edit_text(
                    text,
                    reply_markup=get_telegram_channel_info_keyboard(channel_id),
                    parse_mode="HTML"
                )
                return
        
        else:
            await callback_query.answer(f"❌ Неизвестное действие: {action}", show_alert=True)
            return
        
        # Если это просто просмотр информации о канале, показываем информацию
        # if action == "channel_info" and channel_id: # This line is removed as per the edit hint
        #     # Получаем информацию о канале
        #     channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        #     if not channel_info:
        #         await callback_query.answer("❌ Канал не найден", show_alert=True)
        #         return
        #     # Формируем текст с информацией о канале
        #     text = (
        #         f"📢 <b>Канал: {channel_info.channel.title}</b>\n\n"
        #     )
        #     if channel_info.channel.username:
        #         text += f"Username: @{channel_info.channel.username}\n"
        #     text += f"ID: <code>{channel_info.channel.id}</code>\n"
        #     text += f"Тип: {channel_info.channel.type}\n"
        #     text += f"Дайджестов: {len(channel_info.digests)}\n\n"
        #     if channel_info.digests:
        #         text += "<b>Активные дайджесты:</b>\n"
        #         for digest in channel_info.digests:
        #             status = "✅" if digest.is_active else "⏸️"
        #             text += f"{status} {digest.category} - {digest.time}\n"
        #     else:
        #         text += "Дайджесты не настроены"
        #     # Отправляем сообщение с информацией о канале
        #     await callback_query.message.edit_text(
        #         text,
        #         reply_markup=get_telegram_channel_info_keyboard(channel_id),
        #         parse_mode="HTML"
        #     )
        #     return
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в telegram_channel_info_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

# Словарь для временного хранения данных дайджеста по user_id
temp_digest_data = {}
print(f"🔍 DEBUG: temp_digest_data инициализирован: {temp_digest_data}")

async def handle_digest_category_selection(callback_query: types.CallbackQuery):
    """Обработчик выбора категории для дайджеста (без состояния)"""
    print(f"🔍 DEBUG: handle_digest_category_selection вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        category = data['category']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}, category = {category}")
        
        # Получаем информацию о канале для отображения названия
        channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        channel_title = channel_info.channel.title if channel_info else str(channel_id)
        
        text = (
            f"📰 <b>Добавление дайджеста</b>\n\n"
            f"Канал: {channel_title}\n"
            f"Категория: {category}\n\n"
            "Введите время отправки в формате <b>ЧЧ:ММ</b>\n"
            "Например: 14:30, 9:05, 23:45\n\n"
            "⏰ Время должно быть в 24-часовом формате"
        )
        
        print(f"🔍 DEBUG: Отправляем сообщение с текстом: {text[:100]}...")
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_digest_time_input_keyboard(channel_id, category),
            parse_mode="HTML"
        )
        
        print(f"🔍 DEBUG: Сообщение успешно отправлено")
        
        # Показываем сообщение с просьбой ввести время
        await callback_query.answer(
            f"Категория {category} выбрана. Введите время в формате ЧЧ:ММ",
            show_alert=False
        )
        
        # Сохраняем данные в словарь по user_id
        user_id = callback_query.from_user.id
        temp_digest_data[user_id] = {
            'channel_id': channel_id,
            'category': category,
            'type': 'create'
        }
        
        print(f"🔍 DEBUG: temp_digest_data[{user_id}] установлен: {temp_digest_data[user_id]}")
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в handle_digest_category_selection: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def add_digest_callback(callback_query: types.CallbackQuery):
    """Обработчик добавления дайджеста"""
    print(f"🔍 DEBUG: add_digest_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}")
        
        # Получаем список категорий
        categories = get_categories()
        
        print(f"🔍 DEBUG: Получены категории: {categories}")
        
        if not categories:
            await callback_query.answer("❌ Категории не найдены", show_alert=True)
            return
        
        # Получаем информацию о канале для отображения названия
        channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        channel_title = channel_info.channel.title if channel_info else str(channel_id)
        
        text = (
            f"📰 <b>Добавление дайджеста</b>\n\n"
            f"Канал: {channel_title}\n\n"
            "Выберите категорию для дайджеста:"
        )
        
        print(f"🔍 DEBUG: Отправляем сообщение с текстом: {text[:100]}...")
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_digest_category_keyboard(categories, channel_id),
            parse_mode="HTML"
        )
        
        print(f"🔍 DEBUG: Сообщение успешно отправлено")
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в add_digest_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def digest_category_selected_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора категории для дайджеста"""
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        print(f"🔍 DEBUG: callback_data = {callback_query.data}")
        
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        category = data['category']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}, category = {category}")
        
        # Сохраняем данные в состояние
        await state.update_data(channel_id=channel_id, category=category)
        
        # Получаем информацию о канале для отображения названия
        channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        channel_title = channel_info.channel.title if channel_info else str(channel_id)
        
        text = (
            f"📰 <b>Добавление дайджеста</b>\n\n"
            f"Канал: {channel_title}\n"
            f"Категория: {category}\n\n"
            "Введите время отправки в формате <b>ЧЧ:ММ</b>\n"
            "Например: 14:30, 9:05, 23:45\n\n"
            "⏰ Время должно быть в 24-часовом формате"
        )
        
        print(f"🔍 DEBUG: Отправляем сообщение с текстом: {text[:100]}...")
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_digest_time_input_keyboard(channel_id, category),
            parse_mode="HTML"
        )
        
        print(f"🔍 DEBUG: Сообщение успешно отправлено")
        
        # Переходим в состояние ожидания времени
        await state.set_state(TelegramChannelStates.waiting_for_digest_time)
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в digest_category_selected_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def process_digest_time(message: types.Message, state: FSMContext):
    """Обработчик ввода времени для дайджеста"""
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        time_input = message.text.strip()
        
        # Проверяем формат времени
        time_pattern = re.compile(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$')
        if not time_pattern.match(time_input):
            await message.answer(
                "❌ Неверный формат времени!\n\n"
                "Используйте формат <b>ЧЧ:ММ</b>\n"
                "Например: 14:30, 9:05, 23:45\n\n"
                "Попробуйте еще раз:",
                parse_mode="HTML"
            )
            return
        
        # Получаем данные из состояния
        data = await state.get_data()
        channel_id = data.get("channel_id")
        category = data.get("category")
        
        if not channel_id or not category:
            await message.answer("❌ Ошибка: данные не найдены")
            await state.clear()
            return
        
        # Получаем информацию о канале для отображения названия
        channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        channel_title = channel_info.channel.title if channel_info else str(channel_id)
        
        # Добавляем дайджест к каналу
        success = telegram_channels_service.add_digest_to_channel(channel_id, category, time_input)
        
        if success:
            # Получаем id только что добавленного дайджеста
            channel_info = telegram_channels_service.get_channel_by_id(channel_id)
            digest = None
            if channel_info and channel_info.digests:
                for d in channel_info.digests:
                    if d.category == category and d.time == time_input:
                        digest = d
                        break
            if digest:
                await add_digest_job(channel_id, digest.id, category, time_input)
            text = (
                f"✅ <b>Дайджест успешно добавлен!</b>\n\n"
                f"📢 Канал: {channel_title}\n"
                f"🏷️ Категория: {category}\n"
                f"⏰ Время: {time_input}\n\n"
                f"Дайджест будет отправляться ежедневно в {time_input}"
            )
            
            await message.answer(
                text,
                reply_markup=get_digest_success_keyboard(channel_id),
                parse_mode="HTML"
            )
        else:
            text = (
                f"❌ <b>Ошибка при добавлении дайджеста</b>\n\n"
                f"Не удалось добавить дайджест для канала {channel_title}.\n"
                f"Попробуйте еще раз или обратитесь к администратору."
            )
            
            await message.answer(
                text,
                reply_markup=get_digest_error_keyboard(channel_id),
                parse_mode="HTML"
            )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()

async def process_digest_time_no_state(message: types.Message):
    """Обработчик ввода времени для дайджеста без состояния (создание и редактирование)"""
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        time_input = message.text.strip()
        user_id = message.from_user.id
        
        print(f"🔍 DEBUG: process_digest_time_no_state вызван с текстом: {time_input}")
        print(f"🔍 DEBUG: user_id = {user_id}")
        print(f"🔍 DEBUG: temp_digest_data[{user_id}] = {temp_digest_data.get(user_id)}")
        print(f"🔍 DEBUG: Весь словарь temp_digest_data: {temp_digest_data}")
        
        # Проверяем формат времени
        time_pattern = re.compile(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$')
        if not time_pattern.match(time_input):
            await message.answer(
                "❌ Неверный формат времени!\n\n"
                "Используйте формат <b>ЧЧ:ММ</b>\n"
                "Например: 14:30, 9:05, 23:45\n\n"
                "Попробуйте еще раз:",
                parse_mode="HTML"
            )
            return
        
        user_data = temp_digest_data.get(user_id)
        print(f"🔍 DEBUG: user_data = {user_data}")
        
        if not user_data:
            await message.answer("❌ Ошибка: данные не найдены. Выберите действие заново.")
            return
        
        # Определяем тип действия
        action_type = user_data.get('type') or user_data.get('edit_type')
        print(f"🔍 DEBUG: action_type = {action_type}")
        
        if action_type == 'create':
            # Создание нового дайджеста
            channel_id = user_data.get("channel_id")
            category = user_data.get("category")
            
            print(f"🔍 DEBUG: Создание дайджеста - channel_id = {channel_id}, category = {category}")
        
            if not channel_id or not category:
                await message.answer("❌ Ошибка: данные не найдены")
                if user_id in temp_digest_data:
                    del temp_digest_data[user_id]
                return
            
            # Получаем информацию о канале для отображения названия
            channel_info = telegram_channels_service.get_channel_by_id(channel_id)
            channel_title = channel_info.channel.title if channel_info else str(channel_id)
            
            # Добавляем дайджест к каналу
            success = telegram_channels_service.add_digest_to_channel(channel_id, category, time_input)
            
            if success:
                # Получаем id только что добавленного дайджеста
                channel_info = telegram_channels_service.get_channel_by_id(channel_id)
                digest = None
                if channel_info and channel_info.digests:
                    for d in channel_info.digests:
                        if d.category == category and d.time == time_input:
                            digest = d
                            break
                if digest:
                    await add_digest_job(channel_id, digest.id, category, time_input)
                text = (
                    f"✅ <b>Дайджест успешно добавлен!</b>\n\n"
                    f"📢 Канал: {channel_title}\n"
                    f"🏷️ Категория: {category}\n"
                    f"⏰ Время: {time_input}\n\n"
                    f"Дайджест будет отправляться ежедневно в {time_input}"
                )
                
                await message.answer(
                    text,
                    reply_markup=get_digest_success_keyboard(channel_id),
                    parse_mode="HTML"
                )
                
                # Очищаем данные пользователя после успешного добавления
                if user_id in temp_digest_data:
                    del temp_digest_data[user_id]
                return  # Выходим из функции после успешного добавления
            else:
                text = (
                    f"❌ <b>Ошибка при добавлении дайджеста</b>\n\n"
                    f"Не удалось добавить дайджест для канала {channel_title}.\n"
                    f"Попробуйте еще раз или обратитесь к администратору."
                )
                
                await message.answer(
                    text,
                    reply_markup=get_digest_error_keyboard(channel_id),
                    parse_mode="HTML"
                )
                
                # Очищаем данные пользователя после ошибки
                if user_id in temp_digest_data:
                    del temp_digest_data[user_id]
                return  # Выходим из функции после ошибки
                
        elif action_type == 'time':
            # Редактирование времени дайджеста
            channel_id = user_data.get("channel_id")
            digest_id = user_data.get("digest_id")
            
            print(f"🔍 DEBUG: Редактирование времени - channel_id = {channel_id}, digest_id = {digest_id}")
            
            if not channel_id or not digest_id:
                await message.answer("❌ Ошибка: данные не найдены")
                if user_id in temp_digest_data:
                    del temp_digest_data[user_id]
                return
            
            # Обновляем время дайджеста
            success = telegram_channels_service.update_digest(channel_id, digest_id, {"time": time_input})
            
            if success:
                # Получаем категорию для обновления задачи
                channel_info = telegram_channels_service.get_channel_by_id(channel_id)
                digest = None
                if channel_info and channel_info.digests:
                    for d in channel_info.digests:
                        if d.id == digest_id:
                            digest = d
                            break
                if digest:
                    await update_digest_job(channel_id, digest_id, digest.category, time_input)
                await message.answer(
                    f"✅ Время дайджеста успешно изменено на {time_input}!",
                    reply_markup=get_digest_success_keyboard(channel_id)
                )
            else:
                await message.answer(
                    "❌ Ошибка при изменении времени дайджеста",
                    reply_markup=get_digest_error_keyboard(channel_id)
                )
        
        else:
            await message.answer(f"❌ Ошибка: неизвестный тип действия '{action_type}'")
            return
        
        # Очищаем данные пользователя
        if user_id in temp_digest_data:
            del temp_digest_data[user_id]
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в process_digest_time_no_state: {str(e)}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        user_id = message.from_user.id
        if user_id in temp_digest_data:
            del temp_digest_data[user_id]

async def edit_digests_callback(callback_query: types.CallbackQuery):
    """Обработчик редактирования дайджестов"""
    print(f"🔍 DEBUG: edit_digests_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}")
        
        # Получаем информацию о канале с дайджестами
        channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        
        if not channel_info:
            await callback_query.answer("❌ Канал не найден", show_alert=True)
            return
        
        print(f"🔍 DEBUG: Найдено дайджестов: {len(channel_info.digests) if channel_info.digests else 0}")
        
        if not channel_info.digests:
            # Если нет дайджестов, показываем сообщение с информацией о канале
            print(f"🔍 DEBUG: Нет дайджестов, показываем сообщение с информацией о канале")
            
            text = (
                f"📰 <b>Редактирование дайджестов</b>\n\n"
                f"Канал: {channel_info.channel.title}\n\n"
                "Дайджесты не настроены.\n"
                "Сначала добавьте дайджест через кнопку 'Добавить дайджест'."
            )
            
            await callback_query.message.edit_text(
                text,
                reply_markup=get_telegram_channel_info_keyboard(channel_id),
                parse_mode="HTML"
            )
            return
        
        # Преобразуем дайджесты в формат для клавиатуры
        digests_data = []
        for digest in channel_info.digests:
            digests_data.append({
                "id": digest.id,
                "category": digest.category,
                "time": digest.time,
                "is_active": digest.is_active
            })
        
        text = (
            f"📰 <b>Редактирование дайджестов</b>\n\n"
            f"Канал: {channel_info.channel.title}\n"
            f"Всего дайджестов: {len(channel_info.digests)}\n\n"
            "Выберите дайджест для редактирования:"
        )
        
        print(f"🔍 DEBUG: Отправляем сообщение с текстом: {text[:100]}...")
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_digest_list_keyboard(channel_id, digests_data),
            parse_mode="HTML"
        )
        
        print(f"🔍 DEBUG: Сообщение успешно отправлено")
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в edit_digests_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def digest_info_callback(callback_query: types.CallbackQuery):
    """Обработчик информации о конкретном дайджесте"""
    print(f"🔍 DEBUG: digest_info_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        digest_id = data['digest_id']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}, digest_id = {digest_id}")
        
        # Получаем информацию о канале
        channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        
        if not channel_info:
            await callback_query.answer("❌ Канал не найден", show_alert=True)
            return
        
        # Находим нужный дайджест
        digest = None
        for d in channel_info.digests:
            if d.id == digest_id:
                digest = d
                break
        
        if not digest:
            await callback_query.answer("❌ Дайджест не найден", show_alert=True)
            return
        
        text = (
            f"📰 <b>Информация о дайджесте</b>\n\n"
            f"📢 Канал: {channel_info.channel.title}\n"
            f"🏷️ Категория: {digest.category}\n"
            f"⏰ Время: {digest.time}\n"
            f"📊 Статус: {'✅ Активен' if digest.is_active else '⏸️ Неактивен'}\n"
            f"📅 Создан: {digest.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"🔄 Обновлен: {digest.updated_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Выберите действие:"
        )
        
        print(f"🔍 DEBUG: Отправляем сообщение с текстом: {text[:100]}...")
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_digest_info_keyboard(channel_id, digest_id),
            parse_mode="HTML"
        )
        
        print(f"🔍 DEBUG: Сообщение успешно отправлено")
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в digest_info_callback: {str(e)}")
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def edit_digest_time_callback(callback_query: types.CallbackQuery, state: FSMContext = None):
    """Обработчик изменения времени дайджеста"""
    print(f"🔍 DEBUG: edit_digest_time_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        digest_id = data['digest_id']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}, digest_id = {digest_id}")
        
        # Сохраняем данные в словарь по user_id
        user_id = callback_query.from_user.id
        temp_digest_data[user_id] = {
                'channel_id': channel_id,
                'digest_id': digest_id,
            'user_id': user_id,
                'edit_type': 'time'
            }
        
        print(f"🔍 DEBUG: temp_digest_data[{user_id}] установлен: {temp_digest_data[user_id]}")
        print(f"🔍 DEBUG: Весь словарь temp_digest_data: {temp_digest_data}")
        
        text = (
            f"🕐 <b>Изменение времени дайджеста</b>\n\n"
            f"Введите новое время в формате <b>ЧЧ:ММ</b>\n"
            f"Например: 14:30, 9:05, 23:45\n\n"
            f"⏰ Время должно быть в 24-часовом формате"
        )
        
        await callback_query.message.edit_text(
            text,
            parse_mode="HTML"
        )
        
        # Показываем сообщение с просьбой ввести время
        await callback_query.answer(
            "Введите новое время в формате ЧЧ:ММ",
            show_alert=False
        )
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def edit_digest_category_callback(callback_query: types.CallbackQuery, state: FSMContext = None):
    """Обработчик изменения категории дайджеста"""
    print(f"🔍 DEBUG: edit_digest_category_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        digest_id = data['digest_id']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}, digest_id = {digest_id}")
        
        # Сохраняем данные в словарь по user_id
        user_id = callback_query.from_user.id
        temp_digest_data[user_id] = {
                'channel_id': channel_id,
                'digest_id': digest_id,
                'edit_type': 'category'
            }
        
        print(f"🔍 DEBUG: temp_digest_data[{user_id}] установлен: {temp_digest_data[user_id]}")
        
        # Получаем список категорий
        categories = get_categories()
        
        if not categories:
            await callback_query.answer("❌ Категории не найдены", show_alert=True)
            return
        
        text = (
            f"🏷️ <b>Изменение категории дайджеста</b>\n\n"
            f"Выберите новую категорию:"
        )
        
        # Создаем клавиатуру для выбора категории при редактировании
        from bot.keyboards.inline_keyboards import get_digest_edit_category_keyboard
        keyboard = get_digest_edit_category_keyboard(categories, channel_id, digest_id)
        
        await callback_query.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # Показываем сообщение с просьбой выбрать категорию
        await callback_query.answer(
            "Выберите новую категорию",
            show_alert=False
        )
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def edit_digest_category_select_callback(callback_query: types.CallbackQuery):
    """Обработчик выбора новой категории при редактировании дайджеста"""
    print(f"🔍 DEBUG: edit_digest_category_select_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        digest_id = data['digest_id']
        category = data['category']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}, digest_id = {digest_id}, category = {category}")
        
        # Обновляем категорию дайджеста
        success = telegram_channels_service.update_digest(channel_id, digest_id, {"category": category})
        
        if success:
            # Получаем новое время для обновления задачи
            channel_info = telegram_channels_service.get_channel_by_id(channel_id)
            digest = None
            if channel_info and channel_info.digests:
                for d in channel_info.digests:
                    if d.id == digest_id:
                        digest = d
                        break
            if digest:
                await update_digest_job(channel_id, digest_id, category, digest.time)
            await callback_query.answer(f"✅ Категория дайджеста успешно изменена на '{category}'!")
            
            # Возвращаемся к информации о дайджесте
            await digest_info_callback(callback_query)
        else:
            await callback_query.answer("❌ Ошибка при изменении категории дайджеста", show_alert=True)
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def delete_digest_callback(callback_query: types.CallbackQuery):
    """Обработчик удаления дайджеста"""
    print(f"🔍 DEBUG: delete_digest_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        digest_id = data['digest_id']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}, digest_id = {digest_id}")
        
        # Получаем информацию о канале
        channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        
        if not channel_info:
            await callback_query.answer("❌ Канал не найден", show_alert=True)
            return
        
        # Находим нужный дайджест
        digest = None
        for d in channel_info.digests:
            if d.id == digest_id:
                digest = d
                break
        
        if not digest:
            await callback_query.answer("❌ Дайджест не найден", show_alert=True)
            return
        
        text = (
            f"🗑️ <b>Удаление дайджеста</b>\n\n"
            f"📢 Канал: {channel_info.channel.title}\n"
            f"🏷️ Категория: {digest.category}\n"
            f"⏰ Время: {digest.time}\n\n"
            f"⚠️ <b>Внимание!</b> Это действие нельзя отменить.\n\n"
            f"Вы уверены, что хотите удалить этот дайджест?"
        )
        
        await callback_query.message.edit_text(
            text,
            reply_markup=get_confirm_delete_digest_keyboard(channel_id, digest_id),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def confirm_delete_digest_callback(callback_query: types.CallbackQuery):
    """Обработчик подтверждения удаления дайджеста"""
    print(f"🔍 DEBUG: confirm_delete_digest_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        digest_id = data['digest_id']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}, digest_id = {digest_id}")
        
        # Удаляем дайджест
        success = telegram_channels_service.delete_digest(channel_id, digest_id)
        
        if success:
            await remove_digest_job(digest_id)
            await callback_query.answer("✅ Дайджест успешно удален!")
            
            # Возвращаемся к списку дайджестов
            await edit_digests_callback(callback_query)
        else:
            await callback_query.answer("❌ Ошибка при удалении дайджеста", show_alert=True)
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def process_digest_edit_time(message: types.Message, state: FSMContext):
    """Обработчик изменения времени дайджеста"""
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        time_input = message.text.strip()
        
        # Проверяем формат времени
        time_pattern = re.compile(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$')
        if not time_pattern.match(time_input):
            await message.answer(
                "❌ Неверный формат времени!\n\n"
                "Используйте формат <b>ЧЧ:ММ</b>\n"
                "Например: 14:30, 9:05, 23:45\n\n"
                "Попробуйте еще раз:",
                parse_mode="HTML"
            )
            return
        
        # Получаем данные из состояния
        data = await state.get_data()
        channel_id = data.get("channel_id")
        digest_id = data.get("digest_id")
        
        if not channel_id or not digest_id:
            await message.answer("❌ Ошибка: данные не найдены")
            await state.clear()
            return
        
        # Обновляем время дайджеста
        success = telegram_channels_service.update_digest(channel_id, digest_id, {"time": time_input})
        
        if success:
            # Получаем категорию для обновления задачи
            channel_info = telegram_channels_service.get_channel_by_id(channel_id)
            digest = None
            if channel_info and channel_info.digests:
                for d in channel_info.digests:
                    if d.id == digest_id:
                        digest = d
                        break
            if digest:
                await update_digest_job(channel_id, digest_id, digest.category, time_input)
            await message.answer(
                f"✅ Время дайджеста успешно изменено на {time_input}!",
                reply_markup=get_digest_success_keyboard(channel_id)
            )
        else:
            await message.answer(
                "❌ Ошибка при изменении времени дайджеста",
                reply_markup=get_digest_error_keyboard(channel_id)
            )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()

async def process_digest_edit_category(message: types.Message, state: FSMContext):
    """Обработчик изменения категории дайджеста"""
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        category_input = message.text.strip()
        
        # Получаем данные из состояния
        data = await state.get_data()
        channel_id = data.get("channel_id")
        digest_id = data.get("digest_id")
        
        if not channel_id or not digest_id:
            await message.answer("❌ Ошибка: данные не найдены")
            await state.clear()
            return
        
        # Обновляем категорию дайджеста
        success = telegram_channels_service.update_digest(channel_id, digest_id, {"category": category_input})
        
        if success:
            await message.answer(
                f"✅ Категория дайджеста успешно изменена на '{category_input}'!",
                reply_markup=get_digest_success_keyboard(channel_id)
            )
        else:
            await message.answer(
                "❌ Ошибка при изменении категории дайджеста",
                reply_markup=get_digest_error_keyboard(channel_id)
            )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()

async def process_digest_edit_time_no_state(message: types.Message):
    """Обработчик изменения времени дайджеста без состояния"""
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        time_input = message.text.strip()
        user_id = message.from_user.id
        
        print(f"🔍 DEBUG: process_digest_edit_time_no_state вызван с текстом: {time_input}")
        print(f"🔍 DEBUG: user_id = {user_id}")
        print(f"🔍 DEBUG: temp_digest_data[{user_id}] = {temp_digest_data.get(user_id)}")
        print(f"🔍 DEBUG: Весь словарь temp_digest_data: {temp_digest_data}")
        
        # Проверяем формат времени
        time_pattern = re.compile(r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$')
        if not time_pattern.match(time_input):
            await message.answer(
                "❌ Неверный формат времени!\n\n"
                "Используйте формат <b>ЧЧ:ММ</b>\n"
                "Например: 14:30, 9:05, 23:45\n\n"
                "Попробуйте еще раз:",
                parse_mode="HTML"
            )
            return
        
        user_data = temp_digest_data.get(user_id)
        print(f"🔍 DEBUG: user_data = {user_data}")
        
        if not user_data:
            await message.answer("❌ Ошибка: данные не найдены. Выберите действие заново.")
            return
        
        if user_data.get('edit_type') != 'time':
            await message.answer(f"❌ Ошибка: неверный тип редактирования. Ожидается 'time', получено '{user_data.get('edit_type')}'")
            return
        
        print(f"🔍 DEBUG: edit_type = {user_data.get('edit_type')}")
        
        channel_id = user_data.get("channel_id")
        digest_id = user_data.get("digest_id")
        
        print(f"🔍 DEBUG: channel_id = {channel_id}, digest_id = {digest_id}")
        
        if not channel_id or not digest_id:
            await message.answer("❌ Ошибка: данные не найдены")
            if user_id in temp_digest_data:
                del temp_digest_data[user_id]
            return
        
        # Обновляем время дайджеста
        success = telegram_channels_service.update_digest(channel_id, digest_id, {"time": time_input})
        
        if success:
            # Получаем категорию для обновления задачи
            channel_info = telegram_channels_service.get_channel_by_id(channel_id)
            digest = None
            if channel_info and channel_info.digests:
                for d in channel_info.digests:
                    if d.id == digest_id:
                        digest = d
                        break
            if digest:
                await update_digest_job(channel_id, digest_id, digest.category, time_input)
            await message.answer(
                f"✅ Время дайджеста успешно изменено на {time_input}!",
                reply_markup=get_digest_success_keyboard(channel_id)
            )
        else:
            await message.answer(
                "❌ Ошибка при изменении времени дайджеста",
                reply_markup=get_digest_error_keyboard(channel_id)
            )
        
        # Очищаем данные пользователя
        if user_id in temp_digest_data:
            del temp_digest_data[user_id]
        
    except Exception as e:
        print(f"🔍 DEBUG: Ошибка в process_digest_edit_time_no_state: {str(e)}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        user_id = message.from_user.id
        if user_id in temp_digest_data:
            del temp_digest_data[user_id]

async def process_digest_edit_category_no_state(message: types.Message):
    """Обработчик изменения категории дайджеста без состояния"""
    if not await has_admin_permissions(message.from_user.id, message.from_user.username):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        category_input = message.text.strip()
        user_id = message.from_user.id
        
        user_data = temp_digest_data.get(user_id)
        if not user_data or user_data.get('edit_type') != 'category':
            await message.answer("❌ Ошибка: неверный тип редактирования")
            return
        
        channel_id = user_data.get("channel_id")
        digest_id = user_data.get("digest_id")
        
        if not channel_id or not digest_id:
            await message.answer("❌ Ошибка: данные не найдены")
            if user_id in temp_digest_data:
                del temp_digest_data[user_id]
            return
        
        # Обновляем категорию дайджеста
        success = telegram_channels_service.update_digest(channel_id, digest_id, {"category": category_input})
        
        if success:
            # Получаем новое время для обновления задачи
            channel_info = telegram_channels_service.get_channel_by_id(channel_id)
            digest = None
            if channel_info and channel_info.digests:
                for d in channel_info.digests:
                    if d.id == digest_id:
                        digest = d
                        break
            if digest:
                await update_digest_job(channel_id, digest_id, category_input, digest.time)
            await message.answer(
                f"✅ Категория дайджеста успешно изменена на '{category_input}'!",
                reply_markup=get_digest_success_keyboard(channel_id)
            )
        else:
            await message.answer(
                "❌ Ошибка при изменении категории дайджеста",
                reply_markup=get_digest_error_keyboard(channel_id)
            )
        
        # Очищаем данные пользователя
        if user_id in temp_digest_data:
            del temp_digest_data[user_id]
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        user_id = message.from_user.id
        if user_id in temp_digest_data:
            del temp_digest_data[user_id]

async def test_digest_callback(callback_query: types.CallbackQuery):
    """Обработчик тестирования дайджеста"""
    print(f"🔍 DEBUG: test_digest_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
        # Извлекаем данные из callback_data
        action, data = parse_short_callback(callback_query.data)
        channel_id = data['channel_id']
        digest_id = data['digest_id']
        
        print(f"🔍 DEBUG: action = {action}, channel_id = {channel_id}, digest_id = {digest_id}")
        
        # Получаем информацию о канале
        channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        
        if not channel_info:
            await callback_query.answer("❌ Канал не найден", show_alert=True)
            return
        
        # Находим нужный дайджест
        digest = None
        for d in channel_info.digests:
            if d.id == digest_id:
                digest = d
                break
        
        if not digest:
            await callback_query.answer("❌ Дайджест не найден", show_alert=True)
            return
        
        # Отправляем тестовый дайджест
        from celery_app.tasks.digest_tasks import send_test_digest
        
        # Запускаем задачу отправки тестового дайджеста
        task = send_test_digest.delay(channel_id, digest.category)
        
        await callback_query.answer(
            f"✅ Тестовый дайджест запущен! Task ID: {task.id}",
            show_alert=True
        )
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)

async def schedule_digests_now_callback(callback_query: types.CallbackQuery):
    """Обработчик ручного планирования дайджестов"""
    print(f"🔍 DEBUG: schedule_digests_now_callback вызван с callback_data = {callback_query.data}")
    
    if not await has_admin_permissions(callback_query.from_user.id, callback_query.from_user.username):
        await callback_query.answer("❌ Доступ запрещен", show_alert=True)
        return
    
    try:
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
    # Регистрируем обработчик для инициализации расписания
    dp.callback_query.register(initialize_schedule_callback, lambda c: c.data.startswith('digest_')) 
    # Исправлено: ограничиваем хендлеры только нужными состояниями FSM
    dp.message.register(process_digest_edit_time_no_state, TelegramChannelStates.editing_digest_time)
    dp.message.register(process_digest_edit_category_no_state, TelegramChannelStates.editing_digest_category) 