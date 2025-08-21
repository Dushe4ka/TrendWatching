from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from bot.states.states import CustomStates
from bot.utils.misc import category_to_callback, callback_to_category
from database import get_categories
from celery_app.tasks.trend_analysis_tasks import analyze_trend_task
from celery_app.tasks.news_tasks import analyze_news_task
from celery_app.tasks.weekly_news_tasks import analyze_weekly_news_task
from aiogram3_calendar import SimpleCalendar, simple_cal_callback
from bot.keyboards.inline_keyboards import (
    get_analysis_menu_keyboard,
    get_analysis_digest_menu_keyboard,
    get_analysis_category_keyboard
)

async def menu_analysis_callback(callback_query: types.CallbackQuery):
    """Обработчик меню анализа"""
    keyboard = get_analysis_menu_keyboard()
    await callback_query.message.edit_text(
        "📊 Анализ:\nВыберите действие:",
        reply_markup=keyboard
    )

async def analysis_digest_menu_callback(callback_query: types.CallbackQuery):
    """Обработчик меню дайджестов"""
    keyboard = get_analysis_digest_menu_keyboard()
    await callback_query.message.edit_text(
        "📰 Дайджест новостей:\nВыберите тип:",
        reply_markup=keyboard
    )

# Анализ по запросу
async def analysis_query_category_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора категории для анализа по запросу"""
    categories = get_categories()
    keyboard = get_analysis_category_keyboard(categories, "analysis_query_cat", "menu_analysis")
    await callback_query.message.edit_text(
        "Выберите категорию для анализа:",
        reply_markup=keyboard
    )
    await state.set_state(CustomStates.analysis_query_category)

async def analysis_query_input_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик ввода запроса для анализа"""
    category_hash = callback_query.data.replace("analysis_query_cat_", "")
    categories = get_categories()
    category = callback_to_category(category_hash, categories)
    await state.update_data(category=category)
    await callback_query.message.edit_text(
        f"Вы выбрали категорию: {category}\nВведите ваш запрос:",
    )
    await state.set_state(CustomStates.analysis_query_input)

async def analysis_query_run(message: types.Message, state: FSMContext):
    """Обработчик запуска анализа по запросу"""
    data = await state.get_data()
    category = data.get("category")
    user_query = message.text.strip()
    
    # Создаем клавиатуру с кнопкой "Назад"
    from ..keyboards.inline_keyboards import get_back_to_main_menu_keyboard
    
    await message.answer("⏳ Анализируем материалы... Ожидайте результат в течении получаса.", 
                        reply_markup=get_back_to_main_menu_keyboard())
    analyze_trend_task.delay(category=category, user_query=user_query, chat_id=message.chat.id)
    await state.clear()

# Ежедневный дайджест
async def analysis_daily_category_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора категории для ежедневного дайджеста"""
    categories = get_categories()
    keyboard = get_analysis_category_keyboard(categories, "analysis_daily_cat", "analysis_digest_menu")
    await callback_query.message.edit_text(
        "Выберите категорию для ежедневного дайджеста:",
        reply_markup=keyboard
    )
    await state.set_state(CustomStates.analysis_daily_category)

async def analysis_daily_date_input_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора даты для ежедневного дайджеста"""
    category_hash = callback_query.data.replace("analysis_daily_cat_", "")
    categories = get_categories()
    category = callback_to_category(category_hash, categories)
    await state.update_data(category=category)
    await callback_query.message.edit_text(
        f"Вы выбрали категорию: {category}\nВыберите дату:",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(CustomStates.analysis_daily_date)

async def process_daily_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    """Обработчик календаря для ежедневного дайджеста"""
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        data = await state.get_data()
        category = data.get("category")
        date_str = date.strftime("%Y-%m-%d")
        
        # Создаем клавиатуру с кнопкой "Назад"
        from ..keyboards.inline_keyboards import get_back_to_main_menu_keyboard
        
        await callback_query.message.answer("⏳ Формируем ежедневный дайджест... Ожидайте результат в течении получаса.", 
                                          reply_markup=get_back_to_main_menu_keyboard())
        analyze_news_task.delay(category=category, analysis_date=date_str, chat_id=callback_query.message.chat.id)
        await state.clear()

# Еженедельный дайджест
async def analysis_weekly_category_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора категории для еженедельного дайджеста"""
    categories = get_categories()
    keyboard = get_analysis_category_keyboard(categories, "analysis_weekly_cat", "analysis_digest_menu")
    await callback_query.message.edit_text(
        "Выберите категорию для еженедельного дайджеста:",
        reply_markup=keyboard
    )
    await state.set_state(CustomStates.analysis_weekly_category)

async def analysis_weekly_date_input_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора даты для еженедельного дайджеста"""
    category_hash = callback_query.data.replace("analysis_weekly_cat_", "")
    categories = get_categories()
    category = callback_to_category(category_hash, categories)
    await state.update_data(category=category)
    await callback_query.message.edit_text(
        f"Вы выбрали категорию: {category}\nВыберите начальную дату недели:",
        reply_markup=await SimpleCalendar().start_calendar()
    )
    await state.set_state(CustomStates.analysis_weekly_date)

async def process_weekly_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    """Обработчик календаря для еженедельного дайджеста"""
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        data = await state.get_data()
        category = data.get("category")
        date_str = date.strftime("%Y-%m-%d")
        
        # Создаем клавиатуру с кнопкой "Назад"
        from ..keyboards.inline_keyboards import get_back_to_main_menu_keyboard
        
        await callback_query.message.answer("⏳ Формируем еженедельный дайджест... Ожидайте результат в течении часа.", 
                                          reply_markup=get_back_to_main_menu_keyboard())
        analyze_weekly_news_task.delay(category=category, analysis_start_date=date_str, chat_id=callback_query.message.chat.id)
        await state.clear()

def register_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для анализа"""
    # Основные меню
    dp.callback_query.register(menu_analysis_callback, lambda c: c.data == "menu_analysis")
    dp.callback_query.register(analysis_digest_menu_callback, lambda c: c.data == "analysis_digest_menu")
    
    # Анализ по запросу
    dp.callback_query.register(analysis_query_category_callback, lambda c: c.data == "analysis_query")
    dp.callback_query.register(analysis_query_input_callback, lambda c: c.data.startswith("analysis_query_cat_"))
    dp.message.register(analysis_query_run, CustomStates.analysis_query_input)
    
    # Ежедневный дайджест
    dp.callback_query.register(analysis_daily_category_callback, lambda c: c.data == "analysis_daily")
    dp.callback_query.register(analysis_daily_date_input_callback, lambda c: c.data.startswith("analysis_daily_cat_"))
    dp.callback_query.register(process_daily_calendar, simple_cal_callback.filter(), CustomStates.analysis_daily_date)
    
    # Еженедельный дайджест
    dp.callback_query.register(analysis_weekly_category_callback, lambda c: c.data == "analysis_weekly")
    dp.callback_query.register(analysis_weekly_date_input_callback, lambda c: c.data.startswith("analysis_weekly_cat_"))
    dp.callback_query.register(process_weekly_calendar, simple_cal_callback.filter(), CustomStates.analysis_weekly_date) 