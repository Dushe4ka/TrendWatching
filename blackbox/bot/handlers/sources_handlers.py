import os
import tempfile
import urllib.parse
import requests
from aiogram import Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from bot.states.states import CSVUpload, RSSUpload, TGUpload
from bot.keyboards.inline_keyboards import (
    get_menu_sources_keyboard,
    get_sources_upload_keyboard,
    get_sources_manage_keyboard,
    get_parse_sources_keyboard,
    get_add_more_sources_keyboard,
    create_sources_pagination_keyboard,
    get_csv_upload_back_keyboard,
    get_rss_category_keyboard,
    get_tg_category_keyboard,
    get_custom_category_back_keyboard,
    get_source_input_back_keyboard,
    get_main_menu_back_keyboard
)
from bot.utils.misc import category_to_callback, callback_to_category, get_subscription_id_and_type
from bot.utils.sources_helpers import get_categories_set, get_category_filter, filter_sources_by_category, format_sources_text
from database import (
    get_sources,
    save_sources_db,
    is_source_exists_db,
    delete_source,
    get_categories
)
from csv_sources_reader import process_csv as process_csv_sources

# Конфигурация для auth_service
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")

async def auto_redistribute_channels():
    """Автоматически перераспределяет каналы после добавления источников"""
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/distribute_channels_from_db",
            timeout=30
        )
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        print(f"Ошибка при автоматическом перераспределении каналов: {e}")
        return False

async def auto_clean_duplicates():
    """Автоматически очищает дубликаты каналов"""
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/auth/clean_duplicate_channels",
            timeout=30
        )
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception as e:
        print(f"Ошибка при автоматической очистке дубликатов: {e}")
        return False

async def menu_sources_callback(callback_query: types.CallbackQuery):
    """Обработчик меню источников"""
    keyboard = get_menu_sources_keyboard()
    await callback_query.message.edit_text(
        "📚 Источники:\nВыберите действие:",
        reply_markup=keyboard
    )

async def sources_upload_callback(callback_query: types.CallbackQuery):
    """Обработчик загрузки источников"""
    keyboard = get_sources_upload_keyboard()
    await callback_query.message.edit_text(
        "📥 Загрузка источников:\n❗️Добавленные категории будут видны для подписки/анализа только после успешного парсинга данных❗️\nВыберите тип:",
        reply_markup=keyboard
    )

async def process_csv_file(message: types.Message, state: FSMContext):
    """Обработчик загрузки CSV файла"""
    # Если пользователь отправил не файл, а текст "Назад"
    if message.text and message.text.strip() == "← Назад":
        await message.answer("Вы вернулись в меню загрузки источников.")
        await state.clear()
        return
    
    if not message.document or not message.document.file_name.endswith('.csv'):
        await message.answer(
            "❌ Пожалуйста, отправьте файл в формате CSV.",
            reply_markup=get_csv_upload_back_keyboard()
        )
        return

    # Получаем бота из диспетчера
    from main import bot
    file = await bot.get_file(message.document.file_id)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        await bot.download_file(file.file_path, tmp.name)
        temp_file = tmp.name

    try:
        report = await process_csv_sources(temp_file, message)
        await message.answer(
            f"✅ Загрузка CSV завершена!\n"
            f"Добавлено: {report['added']}\n"
            f"Дубликатов: {report['skipped']}\n"
            f"Ошибок: {report['errors']}"
        )
        
        # Автоматически перераспределяем каналы и очищаем дубликаты
        if report['added'] > 0:
            await message.answer("🔄 Автоматически перераспределяем каналы...")
            redistribute_success = await auto_redistribute_channels()
            clean_success = await auto_clean_duplicates()
            
            if redistribute_success and clean_success:
                await message.answer("✅ Каналы успешно перераспределены и дубликаты очищены!")
            elif redistribute_success:
                await message.answer("✅ Каналы перераспределены, но возникла ошибка при очистке дубликатов")
            else:
                await message.answer("⚠️ Возникла ошибка при перераспределении каналов")
        
        # Предложить парсинг источников
        await message.answer(
            "Хотите запустить парсинг новых источников?",
            reply_markup=get_parse_sources_keyboard()
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке файла: {str(e)}")
    finally:
        os.remove(temp_file)
    await state.clear()

async def upload_csv_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик загрузки CSV"""
    await callback_query.message.edit_text(
        "📤 Пожалуйста, отправьте CSV-файл для массовой загрузки источников.",
        reply_markup=get_csv_upload_back_keyboard()
    )
    await state.set_state(CSVUpload.waiting_for_file)

async def upload_rss_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик загрузки RSS"""
    categories = get_categories()
    keyboard = get_rss_category_keyboard(categories)
    await callback_query.message.edit_text(
        "Выберите категорию для RSS-источника:", reply_markup=keyboard)
    await state.set_state(RSSUpload.waiting_for_category)

async def rss_category_chosen(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора категории для RSS"""
    cat = callback_query.data.replace("rss_cat_", "")
    cat = urllib.parse.unquote(cat)
    if cat == "custom":
        await callback_query.message.edit_text(
            "Введите свою категорию:",
            reply_markup=get_custom_category_back_keyboard("rss")
        )
        await state.set_state(RSSUpload.waiting_for_category)
        await state.update_data(rss_custom=True)
    else:
        await state.update_data(category=cat, rss_custom=False)
        await callback_query.message.edit_text(
            f"Вы выбрали категорию: {cat}\nТеперь введите RSS-ссылку:",
            reply_markup=get_source_input_back_keyboard("rss")
        )
        await state.set_state(RSSUpload.waiting_for_rss)

async def rss_custom_category(message: types.Message, state: FSMContext):
    """Обработчик ввода пользовательской категории для RSS"""
    data = await state.get_data()
    if not data.get("rss_custom"):
        return
    await state.update_data(category=message.text.strip(), rss_custom=False)
    await message.answer(
        f"Вы выбрали категорию: {message.text.strip()}\nТеперь введите RSS-ссылку:",
        reply_markup=get_source_input_back_keyboard("rss")
    )
    await state.set_state(RSSUpload.waiting_for_rss)

async def process_rss_link(message: types.Message, state: FSMContext):
    """Обработчик ввода RSS ссылки"""
    url = message.text.strip()
    data = await state.get_data()
    category = data.get("category", "Общее")
    if not url.startswith("http"):
        await message.answer("❌ Пожалуйста, введите корректную ссылку на RSS-ленту.")
        return
    if is_source_exists_db(url):
        await message.answer("⚠️ Такой источник уже существует (дубликат).")
    else:
        source = {"url": url, "type": "rss", "category": category}
        if save_sources_db(source):
            await message.answer(f"✅ RSS-источник добавлен: {url}")
            
            # Автоматически перераспределяем каналы и очищаем дубликаты
            await message.answer("🔄 Автоматически перераспределяем каналы...")
            redistribute_success = await auto_redistribute_channels()
            clean_success = await auto_clean_duplicates()
            
            if redistribute_success and clean_success:
                await message.answer("✅ Каналы успешно перераспределены и дубликаты очищены!")
            elif redistribute_success:
                await message.answer("✅ Каналы перераспределены, но возникла ошибка при очистке дубликатов")
            else:
                await message.answer("⚠️ Возникла ошибка при перераспределении каналов")
            
            await message.answer(
                "Хотите добавить еще один RSS-источник или завершить?",
                reply_markup=get_add_more_sources_keyboard("rss")
            )
            await state.set_state(RSSUpload.waiting_for_more_rss)
        else:
            await message.answer("❌ Ошибка при сохранении RSS-источника.")
            await state.clear()

async def upload_tg_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик загрузки Telegram каналов"""
    categories = get_categories()
    keyboard = get_tg_category_keyboard(categories)
    await callback_query.message.edit_text(
        "Выберите категорию для Telegram-канала:", reply_markup=keyboard)
    await state.set_state(TGUpload.waiting_for_category)

async def tg_category_chosen(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора категории для Telegram"""
    cat = callback_query.data.replace("tg_cat_", "")
    cat = urllib.parse.unquote(cat)
    if cat == "custom":
        await callback_query.message.edit_text(
            "Введите свою категорию:",
            reply_markup=get_custom_category_back_keyboard("tg")
        )
        await state.set_state(TGUpload.waiting_for_category)
        await state.update_data(tg_custom=True)
    else:
        await state.update_data(category=cat, tg_custom=False)
        await callback_query.message.edit_text(
            f"Вы выбрали категорию: {cat}\nТеперь введите username или ссылку на Telegram-канал:",
            reply_markup=get_source_input_back_keyboard("tg")
        )
        await state.set_state(TGUpload.waiting_for_tg)

async def tg_custom_category(message: types.Message, state: FSMContext):
    """Обработчик ввода пользовательской категории для Telegram"""
    data = await state.get_data()
    if not data.get("tg_custom"):
        return
    await state.update_data(category=message.text.strip(), tg_custom=False)
    await message.answer(
        f"Вы выбрали категорию: {message.text.strip()}\nТеперь введите username или ссылку на Telegram-канал:",
        reply_markup=get_source_input_back_keyboard("tg")
    )
    await state.set_state(TGUpload.waiting_for_tg)

async def process_tg_channel(message: types.Message, state: FSMContext):
    """Обработчик ввода Telegram канала"""
    url = message.text.strip()
    data = await state.get_data()
    category = data.get("category", "Общее")
    
    # Нормализуем URL Telegram канала
    if not url.startswith("http"):
        if url.startswith("@"):
            url = f"https://t.me/{url[1:]}"
        elif not url.startswith("t.me/"):
            url = f"https://t.me/{url}"
        else:
            url = f"https://{url}"
    
    if is_source_exists_db(url):
        await message.answer("⚠️ Такой источник уже существует (дубликат).")
    else:
        source = {"url": url, "type": "telegram", "category": category}
        if save_sources_db(source):
            await message.answer(f"✅ Telegram-канал добавлен: {url}")
            
            # Автоматически перераспределяем каналы и очищаем дубликаты
            await message.answer("🔄 Автоматически перераспределяем каналы...")
            redistribute_success = await auto_redistribute_channels()
            clean_success = await auto_clean_duplicates()
            
            if redistribute_success and clean_success:
                await message.answer("✅ Каналы успешно перераспределены и дубликаты очищены!")
            elif redistribute_success:
                await message.answer("✅ Каналы перераспределены, но возникла ошибка при очистке дубликатов")
            else:
                await message.answer("⚠️ Возникла ошибка при перераспределении каналов")
            
            await message.answer(
                "Хотите добавить еще один Telegram-канал или завершить?",
                reply_markup=get_add_more_sources_keyboard("tg")
            )
            await state.set_state(TGUpload.waiting_for_more_tg)
        else:
            await message.answer("❌ Ошибка при сохранении Telegram-канала.")
            await state.clear()

async def process_more_rss_link(message: types.Message, state: FSMContext):
    """Обработчик добавления дополнительных RSS источников"""
    url = message.text.strip()
    data = await state.get_data()
    category = data.get("category", "Общее")
    if not url.startswith("http"):
        await message.answer("❌ Пожалуйста, введите корректную ссылку на RSS-ленту.")
        return
    if is_source_exists_db(url):
        await message.answer("⚠️ Такой источник уже существует (дубликат).")
    else:
        source = {"url": url, "type": "rss", "category": category}
        if save_sources_db(source):
            await message.answer(f"✅ RSS-источник добавлен: {url}")
            await message.answer(
                "Хотите добавить еще один RSS-источник или завершить?",
                reply_markup=get_add_more_sources_keyboard("rss")
            )
        else:
            await message.answer("❌ Ошибка при сохранении RSS-источника.")
            await state.clear()

async def process_more_tg_channel(message: types.Message, state: FSMContext):
    """Обработчик добавления дополнительных Telegram каналов"""
    tg_id = message.text.strip()
    data = await state.get_data()
    category = data.get("category", "Общее")
    # Привести к username
    if tg_id.startswith("https://t.me/"):
        tg_id = tg_id.replace("https://t.me/", "").replace("/", "")
    tg_id = tg_id.lstrip("@")
    if not tg_id:
        await message.answer("❌ Пожалуйста, введите корректный username или ссылку на Telegram-канал.")
        return
    url = f"https://t.me/{tg_id}"
    if is_source_exists_db(url):
        await message.answer("⚠️ Такой источник уже существует (дубликат).")
    else:
        source = {"url": url, "type": "telegram", "category": category}
        if save_sources_db(source):
            await message.answer(f"✅ Telegram-канал добавлен: {url}")
            await message.answer(
                "Хотите добавить еще один Telegram-канал или завершить?",
                reply_markup=get_add_more_sources_keyboard("tg")
            )
        else:
            await message.answer("❌ Ошибка при сохранении Telegram-канала.")
            await state.clear()

# Обработчики управления источниками
async def sources_manage_callback(callback_query: types.CallbackQuery):
    """Обработчик управления источниками"""
    sources = get_sources()
    categories_set = get_categories_set(sources)
    keyboard = get_sources_manage_keyboard(categories_set)
    
    await callback_query.message.edit_text(
        "Выберите категорию источников для просмотра:",
        reply_markup=keyboard
    )

async def sources_manage_category_callback(callback_query: types.CallbackQuery):
    """Обработчик выбора категории для управления"""
    category_hash = callback_query.data.replace("sources_manage_category_", "")
    sources = get_sources()
    # Используем get_categories() вместо get_categories_set(sources) для консистентности
    categories = get_categories()
    
    # Добавляем логирование для отладки
    print(f"🔍 [DEBUG] category_hash: {category_hash}")
    print(f"🔍 [DEBUG] categories: {categories}")
    
    category_filter = get_category_filter(category_hash, categories)
    
    # Проверяем, что категория найдена
    if category_filter is None:
        print(f"❌ [DEBUG] Категория не найдена для hash: {category_hash}")
        await callback_query.answer("❌ Категория не найдена", show_alert=True)
        return
    
    print(f"✅ [DEBUG] Найдена категория: {category_filter}")
    
    filtered_sources = filter_sources_by_category(sources, category_filter)
    # Передаем category_hash (хеш) вместо category_filter (оригинальное название)
    keyboard = create_sources_pagination_keyboard(filtered_sources, category_hash, page=0)
    total_sources = len(filtered_sources)
    text = format_sources_text(category_filter, total_sources)
    await callback_query.message.edit_text(text, reply_markup=keyboard)

async def delete_source_callback(callback_query: types.CallbackQuery):
    """Обработчик удаления источника"""
    parts = callback_query.data.replace("delete_source_", "").split("_", 2)
    if len(parts) < 3:
        await callback_query.answer("❌ Ошибка при удалении", show_alert=True)
        return
    try:
        category_hash = parts[0]
        source_idx = int(parts[1])
        page = int(parts[2])
    except Exception:
        await callback_query.answer("❌ Ошибка при удалении", show_alert=True)
        return
    
    sources = get_sources()
    # Используем get_categories() для консистентности
    categories = get_categories()
    category_filter = get_category_filter(category_hash, categories)
    
    # Проверяем, что категория найдена
    if category_filter is None:
        await callback_query.answer("❌ Категория не найдена", show_alert=True)
        return
    
    filtered_sources = filter_sources_by_category(sources, category_filter)
    
    if source_idx >= len(filtered_sources):
        await callback_query.answer("❌ Источник не найден", show_alert=True)
        return
    
    url = filtered_sources[source_idx].get('url')
    if delete_source(url):
        await callback_query.answer("✅ Источник удалён", show_alert=False)
    else:
        await callback_query.answer("❌ Ошибка при удалении", show_alert=True)
        return
    
    # Обновляем список, оставаясь на той же странице
    try:
        sources = get_sources()
        # Используем get_categories() для консистентности
        categories = get_categories()
        category_filter = get_category_filter(category_hash, categories)
        filtered_sources = filter_sources_by_category(sources, category_filter)
        total_sources = len(filtered_sources)
        sources_per_page = 10
        total_pages = (total_sources + sources_per_page - 1) // sources_per_page
        if page >= total_pages and total_pages > 0:
            page = total_pages - 1
        keyboard = create_sources_pagination_keyboard(filtered_sources, category_hash, page=page)
        text = format_sources_text(category_filter, total_sources, page, total_pages)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
    except Exception as e:
        await sources_manage_category_callback(callback_query)

async def sources_page_callback(callback_query: types.CallbackQuery):
    """Обработчик пагинации источников"""
    try:
        parts = callback_query.data.replace("sources_page_", "").split("_", 1)
        category_hash = parts[0]
        page = int(parts[1])
        
        # Добавляем логирование для отладки
        print(f"🔍 [DEBUG] sources_page_callback: category_hash={category_hash}, page={page}")
        sources = get_sources()
        # Используем get_categories() для консистентности
        categories = get_categories()
        category_filter = get_category_filter(category_hash, categories)
        
        # Проверяем, что категория найдена
        if category_filter is None:
            await callback_query.answer("❌ Категория не найдена", show_alert=True)
            return
        
        filtered_sources = filter_sources_by_category(sources, category_filter)
        keyboard = create_sources_pagination_keyboard(filtered_sources, category_hash, page=page)
        total_sources = len(filtered_sources)
        sources_per_page = 10
        total_pages = (total_sources + sources_per_page - 1) // sources_per_page
        text = format_sources_text(category_filter, total_sources, page, total_pages)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await callback_query.answer("❌ Ошибка при переходе на страницу")

async def sources_manage_all_category_callback(callback_query: types.CallbackQuery):
    """Обработчик просмотра всех источников"""
    sources = get_sources()
    keyboard = create_sources_pagination_keyboard(sources, category_filter="all", page=0)
    total_sources = len(sources)
    if total_sources == 0:
        text = "🗂 Активные источники:\n\n❌ Источники не найдены"
    else:
        text = f"🗂 Активные источники:\n\n📊 Всего источников: {total_sources}\n📄 Страница 1"
    await callback_query.message.edit_text(text, reply_markup=keyboard)

# Обработчики парсинга
async def parse_sources_menu_callback(callback_query: types.CallbackQuery):
    """Обработчик меню парсинга"""
    await callback_query.message.edit_text(
        "Запустить парсинг всех источников?",
        reply_markup=get_parse_sources_keyboard()
    )

async def parse_sources_confirm_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик подтверждения парсинга"""
    try:
        # Вызываем парсинг через auth_tg_service
        import requests
        auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")
        
        response = requests.post(
            f"{auth_service_url}/parsing/parse_all_sources",
            json={
                "limit": None,
                "chat_id": str(callback_query.message.chat.id)
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            await callback_query.message.edit_text(
                "⏳ Парсинг источников запущен! Вы получите уведомление после завершения.",
                reply_markup=get_main_menu_back_keyboard()
            )
        else:
            await callback_query.message.edit_text(
                "❌ Ошибка при запуске парсинга. Попробуйте позже.",
                reply_markup=get_main_menu_back_keyboard()
            )
    except Exception as e:
        await callback_query.message.edit_text(
            f"❌ Ошибка при запуске парсинга: {str(e)}",
            reply_markup=get_main_menu_back_keyboard()
        )
    
    await state.clear()

async def parse_sources_cancel_callback(callback_query: types.CallbackQuery):
    """Обработчик отмены парсинга"""
    await callback_query.message.edit_text("❌ Парсинг источников отменён.")

async def add_more_sources_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик добавления дополнительных источников"""
    source_type = callback_query.data.replace("add_more_", "")
    data = await state.get_data()
    category = data.get("category", "Общее")
    
    if source_type == "rss":
        await callback_query.message.edit_text(
            f"Категория: {category}\nВведите ссылку на RSS-ленту:",
            reply_markup=get_source_input_back_keyboard("rss")
        )
        await state.set_state(RSSUpload.waiting_for_more_rss)
    elif source_type == "tg":
        await callback_query.message.edit_text(
            f"Категория: {category}\nВведите username или ссылку на Telegram-канал:",
            reply_markup=get_source_input_back_keyboard("tg")
        )
        await state.set_state(TGUpload.waiting_for_more_tg)

async def finish_adding_sources_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик завершения добавления источников"""
    await callback_query.message.edit_text(
        "✅ Добавление источников завершено!",
        reply_markup=get_main_menu_back_keyboard()
    )
    await state.clear()

# Обработчики кнопок "Назад"
async def back_to_sources_upload(callback_query: types.CallbackQuery, state: FSMContext):
    await sources_upload_callback(callback_query, state)

async def back_to_upload_rss(callback_query: types.CallbackQuery, state: FSMContext):
    await upload_rss_callback(callback_query, state)

async def back_to_upload_tg(callback_query: types.CallbackQuery, state: FSMContext):
    await upload_tg_callback(callback_query, state)

async def back_to_upload_rss_from_more(callback_query: types.CallbackQuery, state: FSMContext):
    await upload_rss_callback(callback_query, state)

async def back_to_upload_tg_from_more(callback_query: types.CallbackQuery, state: FSMContext):
    await upload_tg_callback(callback_query, state)

async def noop_callback(callback_query: types.CallbackQuery):
    """Обработчик для кнопок без действия (noop)"""
    await callback_query.answer()

def register_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для работы с источниками"""
    # Основные меню
    dp.callback_query.register(menu_sources_callback, lambda c: c.data == "menu_sources")
    dp.callback_query.register(sources_upload_callback, lambda c: c.data == "sources_upload")
    
    # CSV загрузка
    dp.callback_query.register(upload_csv_callback, lambda c: c.data == "upload_csv")
    dp.message.register(process_csv_file, CSVUpload.waiting_for_file)
    
    # RSS загрузка
    dp.callback_query.register(upload_rss_callback, lambda c: c.data == "upload_rss")
    dp.callback_query.register(rss_category_chosen, lambda c: c.data.startswith("rss_cat_"))
    dp.message.register(rss_custom_category, RSSUpload.waiting_for_category)
    dp.message.register(process_rss_link, RSSUpload.waiting_for_rss)
    dp.message.register(process_more_rss_link, RSSUpload.waiting_for_more_rss)
    
    # Telegram загрузка
    dp.callback_query.register(upload_tg_callback, lambda c: c.data == "upload_tg")
    dp.callback_query.register(tg_category_chosen, lambda c: c.data.startswith("tg_cat_"))
    dp.message.register(tg_custom_category, TGUpload.waiting_for_category)
    dp.message.register(process_tg_channel, TGUpload.waiting_for_tg)
    dp.message.register(process_more_tg_channel, TGUpload.waiting_for_more_tg)
    
    # Управление источниками
    dp.callback_query.register(sources_manage_callback, lambda c: c.data == "sources_manage")
    dp.callback_query.register(sources_manage_category_callback, lambda c: c.data.startswith("sources_manage_category_"))
    dp.callback_query.register(delete_source_callback, lambda c: c.data.startswith("delete_source_"))
    dp.callback_query.register(sources_page_callback, lambda c: c.data.startswith("sources_page_"))
    dp.callback_query.register(sources_manage_all_category_callback, lambda c: c.data == "sources_manage_category_all")
    
    # Парсинг
    dp.callback_query.register(parse_sources_menu_callback, lambda c: c.data == "parse_sources_menu")
    dp.callback_query.register(parse_sources_confirm_callback, lambda c: c.data == "parse_sources_confirm")
    dp.callback_query.register(parse_sources_cancel_callback, lambda c: c.data == "parse_sources_cancel")
    dp.callback_query.register(add_more_sources_callback, lambda c: c.data.startswith("add_more_"))
    dp.callback_query.register(finish_adding_sources_callback, lambda c: c.data == "finish_adding_sources")
    
    # Кнопки "Назад"
    dp.callback_query.register(back_to_sources_upload, lambda c: c.data == "sources_upload")
    dp.callback_query.register(back_to_upload_rss, lambda c: c.data == "upload_rss")
    dp.callback_query.register(back_to_upload_tg, lambda c: c.data == "upload_tg")
    dp.callback_query.register(back_to_upload_rss_from_more, lambda c: c.data == "upload_rss", RSSUpload.waiting_for_more_rss)
    dp.callback_query.register(back_to_upload_tg_from_more, lambda c: c.data == "upload_tg", TGUpload.waiting_for_more_tg)
    
    # Noop кнопки
    dp.callback_query.register(noop_callback, lambda c: c.data.startswith("noop_")) 