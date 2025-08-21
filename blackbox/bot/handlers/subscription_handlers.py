from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from bot.states.states import SubscriptionStates
from bot.utils.misc import get_subscription_id_and_type
from database import (
    get_user_subscription,
    update_user_subscription,
    create_subscription,
    get_categories
)
from bot.keyboards.inline_keyboards import get_subscription_keyboard

async def menu_subscription_callback(callback_query: types.CallbackQuery):
    """Обработчик меню подписки"""
    subscription_id, subscription_type = get_subscription_id_and_type(callback_query)
    # Получаем все категории динамически
    categories = get_categories()
    # Получаем подписки пользователя из БД
    user_subs = get_user_subscription(subscription_id, subscription_type)["categories"]
    keyboard = get_subscription_keyboard(categories, user_subs)
    await callback_query.message.edit_text(
        "🔔 Подписка на ежедневный дайджест:\n❗️Отправка дайджеста в промежутке с 14:00 до 15:00❗️\n\n✅ - категории, на которые вы подписаны\n\nВыберите категории:",
        reply_markup=keyboard
    )

async def toggle_subscription_callback(callback_query: types.CallbackQuery):
    """Обработчик переключения подписки"""
    subscription_id, subscription_type = get_subscription_id_and_type(callback_query)
    cat = callback_query.data.replace("toggle_sub_", "")
    # Получаем текущие категории пользователя
    user_subs = get_user_subscription(subscription_id, subscription_type)["categories"]
    # Добавляем или убираем категорию
    if cat in user_subs:
        user_subs.remove(cat)
    else:
        user_subs.append(cat)
    # Обновляем в БД
    update_user_subscription(subscription_id, subscription_type, user_subs)
    # Получаем все категории динамически
    categories = get_categories()
    keyboard = get_subscription_keyboard(categories, user_subs)
    await callback_query.message.edit_text(
        "🔔 Подписка на ежедневный дайджест:\n❗️Отправка дайджеста в промежутке с 14:00 до 15:00❗️\n\n✅ - категории, на которые вы подписаны\n\nВыберите категории:",
        reply_markup=keyboard
    )

async def process_subscription_category(message: types.Message, state: FSMContext):
    """Обработчик выбора категории для подписки"""
    category = message.text
    
    # Проверяем существующую подписку
    subscription_id, subscription_type = get_subscription_id_and_type(message)
    subscription = get_user_subscription(subscription_id, subscription_type)
    
    if subscription:
        # Обновляем существующую подписку
        categories = subscription.get('categories', [])
        if category in categories:
            categories.remove(category)
            await message.answer(f"✅ Отписались от категории: {category}")
        else:
            categories.append(category)
            await message.answer(f"✅ Подписались на категорию: {category}")
        
        update_user_subscription(subscription_id, subscription_type, categories)
    else:
        # Создаем новую подписку с начальной категорией
        if create_subscription(subscription_id, subscription_type, [category]):
            await message.answer(f"✅ Подписались на категорию: {category}")
        else:
            await message.answer("❌ Произошла ошибка при создании подписки")
    
    await state.clear()
    await message.answer(
        "Теперь вы будете получать ежедневные новости по выбранным категориям.",
        reply_markup=types.ReplyKeyboardRemove()
    )

def register_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров для подписок"""
    dp.callback_query.register(menu_subscription_callback, lambda c: c.data == "menu_subscriptions")
    dp.callback_query.register(toggle_subscription_callback, lambda c: c.data.startswith("toggle_sub_"))
    dp.message.register(process_subscription_category, SubscriptionStates.waiting_for_category) 