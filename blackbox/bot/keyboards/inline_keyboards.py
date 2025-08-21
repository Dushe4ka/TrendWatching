from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
# from bot.utils.misc import category_to_callback  # Временно убираем для избежания циклических импортов
from typing import List, Dict, Set, Any
import aiogram.types as types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.utils.callback_utils import create_digest_callback

def category_to_callback(category: str) -> str:
    """Временная функция для избежания циклических импортов"""
    return category.lower().replace(' ', '_').replace('-', '_')

def get_dynamic_main_menu_keyboard(permissions: dict) -> InlineKeyboardMarkup:
    """Создает динамическую клавиатуру главного меню на основе прав пользователя"""
    buttons = []
    
    # Проверяем права и добавляем соответствующие кнопки
    if permissions.get("can_access_sources", False):
        buttons.append(InlineKeyboardButton(text="📚 Источники", callback_data="menu_sources"))
    
    if permissions.get("can_access_analysis", False):
        buttons.append(InlineKeyboardButton(text="📊 Анализ", callback_data="menu_analysis"))
    
    if permissions.get("can_access_subscriptions", False):
        buttons.append(InlineKeyboardButton(text="📰 Подписки", callback_data="menu_subscriptions"))
    
    # Если у пользователя есть права на админские функции, добавляем их
    admin_buttons = []
    if permissions.get("can_manage_telegram_auth", False):
        admin_buttons.append(InlineKeyboardButton(text="🔐 Авторизация", callback_data="auth_menu"))
    
    if permissions.get("can_access_admin_panel", False):
        admin_buttons.append(InlineKeyboardButton(text="⚙️ Админ", callback_data="menu_admin"))
    
    # Формируем клавиатуру
    keyboard_rows = []
    
    # Основные кнопки (по 2 в ряд)
    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        keyboard_rows.append(row)
    
    # Админские кнопки (по 2 в ряд)
    if admin_buttons:
        for i in range(0, len(admin_buttons), 2):
            row = admin_buttons[i:i+2]
            keyboard_rows.append(row)
    
    # Если нет кнопок, добавляем сообщение об отсутствии прав
    if not keyboard_rows:
        keyboard_rows.append([InlineKeyboardButton(text="❌ Нет доступных функций", callback_data="no_access")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

def get_user_main_menu_keyboard():
    """Клавиатура главного меню для обычных пользователей (без админских функций)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📚 Источники", callback_data="menu_sources"),
            InlineKeyboardButton(text="📊 Анализ", callback_data="menu_analysis")
        ],
        [
            InlineKeyboardButton(text="📰 Подписки", callback_data="menu_subscriptions")
        ]
    ])
    return keyboard

def get_admin_main_menu_keyboard():
    """Клавиатура главного меню для администраторов (с админскими функциями)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📚 Источники", callback_data="menu_sources"),
            InlineKeyboardButton(text="📊 Анализ", callback_data="menu_analysis")
        ],
        [
            InlineKeyboardButton(text="📰 Подписки", callback_data="menu_subscriptions"),
            InlineKeyboardButton(text="🔐 Авторизация", callback_data="auth_menu")
        ],
        [
            InlineKeyboardButton(text="⚙️ Админ", callback_data="menu_admin")
        ]
    ])
    return keyboard

def get_menu_sources_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Загрузка", callback_data="sources_upload")],
            [InlineKeyboardButton(text="Просмотр и удаление", callback_data="sources_manage")],
            [InlineKeyboardButton(text="Парсинг источников", callback_data="parse_sources_menu")],
            [InlineKeyboardButton(text="← Назад", callback_data="main_menu")],
        ]
    )
    return keyboard

def get_sources_upload_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="CSV-файл (массовая загрузка)", callback_data="upload_csv")],
            [InlineKeyboardButton(text="RSS-лента (одна ссылка)", callback_data="upload_rss")],
            [InlineKeyboardButton(text="Telegram-канал (один канал)", callback_data="upload_tg")],
            [InlineKeyboardButton(text="← Назад", callback_data="menu_sources")],
        ]
    )
    return keyboard

def get_sources_manage_keyboard(categories: Set[str]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру со списком категорий источников.
    Принимает на вход set() с названиями категорий.
    """
    # Логика сборки кнопок, которая раньше была в хендлере
    category_buttons = [
        [InlineKeyboardButton(text=cat_name, callback_data=f"sources_manage_category_{category_to_callback(cat_name)}")]
        for cat_name in sorted(list(categories)) # Преобразуем set в отсортированный list для цикла
    ]
    
    # Добавляем статические кнопки
    category_buttons.append([InlineKeyboardButton(text="Все", callback_data="sources_manage_category_all")])
    category_buttons.append([InlineKeyboardButton(text="← Назад", callback_data="menu_sources")])
    
    return InlineKeyboardMarkup(inline_keyboard=category_buttons)

def get_parse_sources_keyboard():
    """Создает клавиатуру для парсинга источников"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Принять", callback_data="parse_sources_confirm")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="parse_sources_cancel")],
        ]
    )

def get_add_more_sources_keyboard(source_type: str):
    """Создает клавиатуру для продолжения добавления источников"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Загрузить еще", callback_data=f"add_more_{source_type}")],
            [InlineKeyboardButton(text="Запустить парсинг", callback_data="parse_sources_confirm")],
            [InlineKeyboardButton(text="Завершить", callback_data="finish_adding_sources")],
        ]
    )

def create_sources_pagination_keyboard(sources: List[Dict], category_filter: str = "all", page: int = 0, sources_per_page: int = 10):
    """Создает клавиатуру с пагинацией для управления источниками"""
    total_sources = len(sources)
    total_pages = (total_sources + sources_per_page - 1) // sources_per_page
    
    if total_sources == 0:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="← Назад", callback_data="menu_sources")]]
        )
    
    # Ограничиваем страницу
    page = max(0, min(page, total_pages - 1))
    
    # Получаем источники для текущей страницы
    start_idx = page * sources_per_page
    end_idx = min(start_idx + sources_per_page, total_sources)
    page_sources = sources[start_idx:end_idx]
    
    # Создаем кнопки для источников
    keyboard_rows = []
    for i, src in enumerate(page_sources):
        source_idx = start_idx + i
        source_type = src.get('type', '?')
        source_url = src.get('url', '')
        # Обрезаем URL для отображения
        display_url = source_url[:30] + "..." if len(source_url) > 30 else source_url
        
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{source_type}: {display_url}", 
                callback_data=f"noop_{category_to_callback(category_filter)}_{source_idx}_{page}"
            ),
            InlineKeyboardButton(
                text="❌", 
                callback_data=f"delete_source_{category_to_callback(category_filter)}_{source_idx}_{page}"
            )
        ])
    
    # Добавляем навигационные кнопки
    nav_buttons = []
    
    # Кнопка "Предыдущая страница"
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"sources_page_{category_to_callback(category_filter)}_{page-1}"))
    
    # Информация о странице
    nav_buttons.append(InlineKeyboardButton(
        text=f"{page+1}/{total_pages}", 
        callback_data="noop_page_info"
    ))
    
    # Кнопка "Следующая страница"
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"sources_page_{category_to_callback(category_filter)}_{page+1}"))
    
    if nav_buttons:
        keyboard_rows.append(nav_buttons)
    
    # Кнопка "Назад"
    keyboard_rows.append([InlineKeyboardButton(text="← Назад", callback_data="menu_sources")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

# Клавиатуры для анализа
def get_analysis_menu_keyboard():
    """Клавиатура меню анализа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Анализ по запросу", callback_data="analysis_query")],
            [InlineKeyboardButton(text="Дайджест новостей", callback_data="analysis_digest_menu")],
            [InlineKeyboardButton(text="← Назад", callback_data="main_menu")],
        ]
    )

def get_analysis_digest_menu_keyboard():
    """Клавиатура меню дайджестов"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ежедневный", callback_data="analysis_daily")],
            [InlineKeyboardButton(text="Еженедельный", callback_data="analysis_weekly")],
            [InlineKeyboardButton(text="← Назад", callback_data="menu_analysis")],
        ]
    )

def get_analysis_category_keyboard(categories: List[str], callback_prefix: str, back_callback: str):
    """Клавиатура выбора категории для анализа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=cat, callback_data=f"{callback_prefix}_{category_to_callback(cat)}")]
                         for cat in categories] +
        [[InlineKeyboardButton(text="← Назад", callback_data=back_callback)]]
    )

# Клавиатуры для подписок
def get_subscription_keyboard(categories: List[str], user_subs: List[str]):
    """Клавиатура управления подписками"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=(cat + (" ✅" if cat in user_subs else "")),
                callback_data=f"toggle_sub_{cat}")]
            for cat in categories
        ] + [[InlineKeyboardButton(text="← Назад", callback_data="main_menu")]]
    )

# Клавиатуры для авторизации
def get_auth_menu_keyboard():
    """Клавиатура для меню авторизации"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Добавить аккаунт", callback_data="add_new_account"),
            InlineKeyboardButton(text="📊 Статус авторизации", callback_data="check_auth_status")
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить аккаунт", callback_data="delete_account")
        ],
        [
            InlineKeyboardButton(text="🔧 Сервис авторизации", callback_data="auth_service_menu")
        ],
        [
            InlineKeyboardButton(text="← Главное меню", callback_data="main_menu")
        ]
    ])
    return keyboard

def get_auth_service_menu_keyboard():
    """Клавиатура для меню сервиса авторизации"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📺 Распределить каналы", callback_data="distribute_channels"),
            InlineKeyboardButton(text="🧹 Очистить дубликаты", callback_data="clean_duplicates")
        ],
        [
            InlineKeyboardButton(text="🗑️ Очистить все каналы", callback_data="clear_all_channels")
        ],
        [
            InlineKeyboardButton(text="← Назад", callback_data="auth_menu")
        ]
    ])
    return keyboard

def get_auth_service_keyboard():
    """Клавиатура для сервиса авторизации"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статус сессий", callback_data="auth_service_status"),
            InlineKeyboardButton(text="🔍 Проверить все", callback_data="auth_service_check_all")
        ],
        [
            InlineKeyboardButton(text="📋 Отладка", callback_data="auth_service_debug"),
            InlineKeyboardButton(text="🚀 Парсинг", callback_data="auth_service_parsing")
        ],
        [
            InlineKeyboardButton(text="📺 Распределить", callback_data="auth_service_distribute"),
            InlineKeyboardButton(text="🧹 Очистить", callback_data="auth_service_clean")
        ],
        [
            InlineKeyboardButton(text="← Назад", callback_data="menu_admin")
        ]
    ])
    return keyboard

def get_parsing_menu_keyboard():
    """Создает клавиатуру для парсинга источников"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Парсинг всех источников", callback_data="auth_service_parse_all")],
        [InlineKeyboardButton(text="📡 Парсинг RSS", callback_data="auth_service_parse_rss")],
        [InlineKeyboardButton(text="📱 Парсинг Telegram", callback_data="auth_service_parse_telegram")],
        [InlineKeyboardButton(text="📊 Статистика парсинга", callback_data="auth_service_parsing_status")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="auth_service_menu")]
    ])

def get_session_management_keyboard():
    """Создает клавиатуру для управления сессиями"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Общий статус", callback_data="auth_service_status")],
        [InlineKeyboardButton(text="🔍 Проверить все", callback_data="auth_service_check_all")],
        [InlineKeyboardButton(text="📋 Отладка", callback_data="auth_service_debug")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="auth_service_menu")]
    ])

# Клавиатуры для источников (дополнительные)
def get_csv_upload_back_keyboard():
    """Клавиатура для возврата при загрузке CSV"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="sources_upload")]
        ]
    )

def get_rss_category_keyboard(categories: List[str]):
    """Клавиатура выбора категории для RSS"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"rss_cat_{cat}")] for cat in categories
        ] + [
            [InlineKeyboardButton(text="Своя категория", callback_data="rss_cat_custom")],
            [InlineKeyboardButton(text="← Назад", callback_data="sources_upload")]
        ]
    )

def get_tg_category_keyboard(categories: List[str]):
    """Клавиатура выбора категории для Telegram"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"tg_cat_{cat}")] for cat in categories
        ] + [
            [InlineKeyboardButton(text="Своя категория", callback_data="tg_cat_custom")],
            [InlineKeyboardButton(text="← Назад", callback_data="sources_upload")]
        ]
    )

def get_custom_category_back_keyboard(source_type: str):
    """Клавиатура возврата при вводе пользовательской категории"""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="← Назад", callback_data=f"upload_{source_type}")]]
    )

def get_source_input_back_keyboard(source_type: str):
    """Клавиатура возврата при вводе источника"""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="← Назад", callback_data=f"upload_{source_type}")]]
    )

def get_main_menu_back_keyboard():
    """Клавиатура возврата в главное меню"""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="← В главное меню", callback_data="main_menu")]]
    )

def get_role_management_keyboard():
    """Клавиатура для управления ролями"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="➕ Создать роль", callback_data="create_role"),
            types.InlineKeyboardButton(text="🔧 Редактировать", callback_data="edit_role")
        ],
        [
            types.InlineKeyboardButton(text="📋 Список ролей", callback_data="list_roles"),
            types.InlineKeyboardButton(text="👥 Пользователи", callback_data="list_users")
        ],
        [
            types.InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
    ])
    return keyboard


def get_role_creation_keyboard():
    """Клавиатура для создания роли с кнопкой назад"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="role_management")
        ]
    ])
    return keyboard


def get_role_edit_keyboard(role_name: str):
    """Клавиатура для редактирования роли"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🔧 Изменить разрешения", callback_data="edit_permissions"),
            types.InlineKeyboardButton(text="🗑️ Удалить роль", callback_data="delete_role")
        ],
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="edit_role")
        ]
    ])
    return keyboard


def get_role_edit_list_keyboard():
    """Клавиатура для возврата в список ролей для редактирования"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="edit_role")
        ]
    ])
    return keyboard


def get_permission_keyboard(available_permissions: list, selected_permissions: dict):
    """Клавиатура для выбора разрешений (с русскими описаниями)"""
    permission_descriptions = {
        "can_access_sources": "Доступ к источникам",
        "can_access_analysis": "Доступ к анализу",
        "can_access_subscriptions": "Доступ к подпискам",
        "can_manage_telegram_auth": "Управление авторизацией",
        "can_access_admin_panel": "Доступ к админ панели"
    }
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    # Группируем разрешения по 2 в ряд
    for i in range(0, len(available_permissions), 2):
        row = []
        # Первое разрешение в ряду
        perm1 = available_permissions[i]
        is_selected1 = selected_permissions.get(perm1, False)
        status1 = "✅" if is_selected1 else "❌"
        desc1 = permission_descriptions.get(perm1, perm1)
        row.append(types.InlineKeyboardButton(
            text=f"{status1} {desc1}",
            callback_data=f"perm_{perm1}"
        ))
        # Второе разрешение в ряду (если есть)
        if i + 1 < len(available_permissions):
            perm2 = available_permissions[i + 1]
            is_selected2 = selected_permissions.get(perm2, False)
            status2 = "✅" if is_selected2 else "❌"
            desc2 = permission_descriptions.get(perm2, perm2)
            row.append(types.InlineKeyboardButton(
                text=f"{status2} {desc2}",
                callback_data=f"perm_{perm2}"
            ))
        keyboard.inline_keyboard.append(row)
    # Кнопки действий
    keyboard.inline_keyboard.append([
        types.InlineKeyboardButton(text="💾 Сохранить", callback_data="save_permissions"),
        types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_previous_step")
    ])
    return keyboard


def get_confirm_keyboard(action: str):
    """Клавиатура для подтверждения действия"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Да, подтверждаю", callback_data=f"confirm_{action}"),
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_role_edit")
        ]
    ])
    return keyboard


def get_admin_panel_keyboard():
    """Клавиатура для админской панели"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🔧 Микросервис", callback_data="auth_service_menu"),
            types.InlineKeyboardButton(text="👥 Роли", callback_data="role_management")
        ],
        [
            types.InlineKeyboardButton(text="📢 Telegram каналы", callback_data="telegram_channels_menu")
        ],
        [
            types.InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
    ])
    return keyboard


def get_user_management_keyboard():
    """Клавиатура для управления пользователями"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="👥 Список пользователей", callback_data="list_users"),
            types.InlineKeyboardButton(text="🔧 Назначить роли", callback_data="assign_roles")
        ],
        [
            types.InlineKeyboardButton(text="🔄 Обновить кэш", callback_data="refresh_cache")
        ],
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="role_management")
        ]
    ])
    return keyboard


def get_back_to_main_menu_keyboard():
    """Клавиатура для возврата в главное меню (альтернативное название)"""
    return get_main_menu_back_keyboard()

# Новые клавиатуры для управления Telegram каналами
def get_telegram_channels_menu_keyboard():
    """Клавиатура для меню управления Telegram каналами"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="📢 Список каналов", callback_data="telegram_channels_list")
        ],
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data="menu_admin")
        ]
    ])
    return keyboard

def get_telegram_channels_list_keyboard(channels: List[Dict[str, Any]]):
    """Клавиатура со списком Telegram каналов"""
    from bot.utils.callback_utils import create_channel_callback
    
    keyboard_rows = []
    
    for channel in channels:
        # Создаем кнопку для каждого канала
        channel_text = f"📢 {channel['title']}"
        if channel.get('username'):
            channel_text += f" (@{channel['username']})"
        
        keyboard_rows.append([
            types.InlineKeyboardButton(
                text=channel_text,
                callback_data=create_channel_callback("channel_info", channel['id'])
            )
        ])
    
    # Кнопка "Назад"
    keyboard_rows.append([
        types.InlineKeyboardButton(text="🔙 Назад", callback_data="telegram_channels_menu")
    ])
    
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

def get_telegram_channel_info_keyboard(channel_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для информации о Telegram канале"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.button(
        text="➕ Добавить дайджест",
        callback_data=create_digest_callback("add_digest", channel_id)
    )
    keyboard.button(
        text="✏️ Редактировать дайджесты",
        callback_data=create_digest_callback("edit_digests", channel_id)
    )
    keyboard.button(
        text="🔄 Инициализировать расписание",
        callback_data=create_digest_callback("initialize_schedule", channel_id)
    )
    keyboard.button(
        text="📊 Проверить расписание",
        callback_data=create_digest_callback("check_schedule", channel_id)
    )
    keyboard.button(
        text="⬅️ Назад к каналам",
        callback_data="telegram_channels_list"
    )
    
    keyboard.adjust(1)
    return keyboard.as_markup()

def get_digest_category_keyboard(categories: List[str], channel_id: int):
    """Клавиатура для выбора категории дайджеста"""
    from bot.utils.callback_utils import create_category_callback
    
    keyboard_rows = []
    
    # Группируем категории по 2 в ряд
    for i in range(0, len(categories), 2):
        row = []
        
        # Первая категория в ряду
        cat1 = categories[i]
        row.append(types.InlineKeyboardButton(
            text=cat1,
            callback_data=create_category_callback("digest_cat", channel_id, cat1)
        ))
        
        # Вторая категория в ряду (если есть)
        if i + 1 < len(categories):
            cat2 = categories[i + 1]
            row.append(types.InlineKeyboardButton(
                text=cat2,
                callback_data=create_category_callback("digest_cat", channel_id, cat2)
            ))
        
        keyboard_rows.append(row)
    
    # Кнопка "Назад"
    from bot.utils.callback_utils import create_channel_callback
    keyboard_rows.append([
        types.InlineKeyboardButton(text="🔙 Назад", callback_data=create_channel_callback("channel_info", channel_id))
    ])
    
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

def get_digest_edit_category_keyboard(categories: List[str], channel_id: int, digest_id: str):
    """Клавиатура для выбора категории при редактировании дайджеста"""
    from bot.utils.callback_utils import create_digest_callback
    
    keyboard_rows = []
    
    # Группируем категории по 2 в ряд
    for i in range(0, len(categories), 2):
        row = []
        
        # Первая категория в ряду
        cat1 = categories[i]
        row.append(types.InlineKeyboardButton(
            text=cat1,
            callback_data=create_digest_callback("edit_digest_category_select", channel_id, digest_id, category=cat1)
        ))
        
        # Вторая категория в ряду (если есть)
        if i + 1 < len(categories):
            cat2 = categories[i + 1]
            row.append(types.InlineKeyboardButton(
                text=cat2,
                callback_data=create_digest_callback("edit_digest_category_select", channel_id, digest_id, category=cat2)
            ))
        
        keyboard_rows.append(row)
    
    # Кнопка "Назад"
    keyboard_rows.append([
        types.InlineKeyboardButton(text="🔙 Назад", callback_data=create_digest_callback("digest_info", channel_id, digest_id))
    ])
    
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

def get_digest_time_input_keyboard(channel_id: int, category: str):
    """Клавиатура для ввода времени дайджеста"""
    from bot.utils.callback_utils import create_channel_callback
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data=create_channel_callback("add_digest", channel_id))
        ]
    ])
    return keyboard

def get_digest_success_keyboard(channel_id: int):
    """Клавиатура для успешного добавления дайджеста"""
    from bot.utils.callback_utils import create_channel_callback
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data=create_channel_callback("channel_info", channel_id))
        ]
    ])
    return keyboard

def get_digest_error_keyboard(channel_id: int):
    """Клавиатура для ошибки при добавлении дайджеста"""
    from bot.utils.callback_utils import create_channel_callback
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data=create_channel_callback("channel_info", channel_id))
        ]
    ])
    return keyboard

def get_digest_list_keyboard(channel_id: int, digests: List[Dict[str, Any]]):
    """Клавиатура со списком дайджестов канала"""
    from bot.utils.callback_utils import create_digest_callback, create_channel_callback
    
    keyboard_rows = []
    
    for digest in digests:
        # Создаем кнопку для каждого дайджеста
        digest_text = f"📰 {digest['category']} - {digest['time']}"
        if not digest.get('is_active', True):
            digest_text += " ⏸️"
        
        keyboard_rows.append([
            types.InlineKeyboardButton(
                text=digest_text,
                callback_data=create_digest_callback("digest_info", channel_id, digest['id'])
            )
        ])
    
    # Кнопка "Назад"
    keyboard_rows.append([
        types.InlineKeyboardButton(text="🔙 Назад", callback_data=create_channel_callback("channel_info", channel_id))
    ])
    
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

def get_digest_info_keyboard(channel_id: int, digest_id: str):
    """Клавиатура для информации о конкретном дайджесте"""
    from bot.utils.callback_utils import create_digest_callback, create_channel_callback
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="🕐 Изменить время", callback_data=create_digest_callback("edit_digest_time", channel_id, digest_id))
        ],
        [
            types.InlineKeyboardButton(text="🏷️ Изменить категорию", callback_data=create_digest_callback("edit_digest_category", channel_id, digest_id))
        ],
        [
            types.InlineKeyboardButton(text="🧪 Тестировать дайджест", callback_data=create_digest_callback("test_digest", channel_id, digest_id))
        ],
        [
            types.InlineKeyboardButton(text="🗑️ Удалить дайджест", callback_data=create_digest_callback("delete_digest", channel_id, digest_id))
        ],
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data=create_channel_callback("edit_digests", channel_id))
        ]
    ])
    return keyboard

def get_confirm_delete_digest_keyboard(channel_id: int, digest_id: str):
    """Клавиатура для подтверждения удаления дайджеста"""
    from bot.utils.callback_utils import create_digest_callback
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Да, удалить", callback_data=create_digest_callback("confirm_delete_digest", channel_id, digest_id))
        ],
        [
            types.InlineKeyboardButton(text="🔙 Назад", callback_data=create_digest_callback("digest_info", channel_id, digest_id))
        ]
    ])
    return keyboard

