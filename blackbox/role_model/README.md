# Ролевая система TrendWatching Bot

## Обзор

Ролевая система обеспечивает контроль доступа к функциям бота на основе ролей пользователей. Система интегрирована с Lark Base для хранения данных о пользователях и их ролях.

## Архитектура

### Основные компоненты

1. **RoleManager** - главный менеджер ролевой системы
2. **BaseUserProvider** - абстрактный класс для провайдеров пользователей
3. **BaseRoleProvider** - абстрактный класс для провайдеров ролей
4. **LarkUserProvider** - провайдер пользователей для Lark Base
5. **LarkRoleProvider** - провайдер ролей (локальное хранилище)

### Структура данных

#### UserInfo
```python
@dataclass
class UserInfo:
    user_id: int
    telegram_username: Optional[str] = None
    role: Optional[str] = None
    is_whitelisted: bool = False
    is_active: bool = True
    company_id: Optional[str] = None
```

#### RolePermissions
```python
@dataclass
class RolePermissions:
    role_name: str
    permissions: Dict[str, bool]
    description: str = ""
```

## Доступные роли

### admin
- **Описание**: Полный доступ ко всем функциям
- **Разрешения**: Все разрешения включены

### manager
- **Описание**: Доступ к управлению источниками и аналитике
- **Разрешения**: 
  - ✅ can_use_analysis
  - ✅ can_manage_sources
  - ✅ can_receive_digest
  - ✅ can_auth_telegram
  - ✅ can_view_statistics
  - ✅ can_export_data
  - ❌ can_create_roles
  - ❌ can_manage_users
  - ❌ can_manage_roles
  - ❌ can_view_logs
  - ❌ can_manage_settings

### analyst
- **Описание**: Доступ к аналитике и дайджестам
- **Разрешения**:
  - ✅ can_use_analysis
  - ✅ can_receive_digest
  - ✅ can_view_statistics
  - ✅ can_export_data
  - ❌ can_manage_sources
  - ❌ can_auth_telegram
  - ❌ can_create_roles
  - ❌ can_manage_users
  - ❌ can_manage_roles
  - ❌ can_view_logs
  - ❌ can_manage_settings

### tester
- **Описание**: Ограниченный доступ для тестирования
- **Разрешения**:
  - ✅ can_use_analysis
  - ❌ Все остальные разрешения

## Доступные разрешения

| Разрешение | Описание |
|------------|----------|
| `can_use_analysis` | Доступ к аналитическим функциям |
| `can_manage_sources` | Управление источниками данных |
| `can_receive_digest` | Получение дайджестов |
| `can_auth_telegram` | Авторизация Telegram аккаунтов |
| `can_create_roles` | Создание новых ролей |
| `can_manage_users` | Управление пользователями |
| `can_view_statistics` | Просмотр статистики |
| `can_export_data` | Экспорт данных |
| `can_manage_roles` | Управление ролями |
| `can_view_logs` | Просмотр логов |
| `can_manage_settings` | Управление настройками |

## Использование

### Инициализация в боте

```python
from config import get_role_system_config
from role_model.lark_provider import LarkUserProvider, LarkRoleProvider
from role_model.role_manager import RoleManager

# Получаем конфигурацию
role_config = get_role_system_config()["lark"]

# Создаем провайдеры
user_provider = LarkUserProvider(
    app_id=role_config["app_id"],
    app_secret=role_config["app_secret"],
    table_app_id=role_config["table_app_id"],
    table_id=role_config["table_id"]
)

role_provider = LarkRoleProvider()

# Создаем менеджер ролей
role_manager = RoleManager(user_provider, role_provider)
```

### Проверка разрешений

```python
# Проверка конкретного разрешения
has_permission = await role_manager.check_permission(user_id, "can_use_analysis")

# Получение всех разрешений пользователя
permissions = await role_manager.get_user_permissions(user_id)

# Получение информации о пользователе
user_info = await role_manager.get_user_info(user_id)
```

### Использование декоратора

```python
from bot.utils.misc import require_permission

@require_permission("can_use_analysis")
async def analysis_handler(message: types.Message):
    # Обработчик будет выполнен только если у пользователя есть разрешение
    pass
```

## Команды бота

### Для всех пользователей
- `/permissions` - показать свои разрешения

### Для администраторов
- `/roles` - список всех ролей
- `/users` - список пользователей
- `/refresh_cache` - обновить кэш пользователей

## Конфигурация

### Переменные окружения

```bash
LARK_APP_ID=cli_a7764cea6af99029
LARK_APP_SECRET=sr8FEkHkNRWfI0OirUCQbg6EeeHv60fg
LARK_TABLE_APP_ID=VpuPbqXvsaVKewsMZe9l7auBgUg
LARK_TABLE_ID=tbliFeTLOkCUpCps
```

### Структура таблицы Lark Base

Таблица должна содержать следующие поля:
- `Telegram` - Telegram username пользователя
- `Роль` - роль пользователя (admin, manager, analyst, tester)
- `Компания` - компания пользователя (опционально)

## Тестирование

### Запуск тестов

```bash
# Общий тест ролевой системы
python tests/test_role_system.py

# Тест конкретного пользователя
python tests/test_role_system.py --user-id 123456789
```

### Тестирование в боте

1. Запустите бота
2. Отправьте команду `/permissions` для проверки своих разрешений
3. Используйте команды `/roles` и `/users` (если есть права)

## Кэширование

Система использует кэширование для оптимизации производительности:

- **Токен доступа**: кэшируется на 1 час
- **Пользователи**: кэшируются на 5 минут
- **Роли**: хранятся локально (не кэшируются)

Для принудительного обновления кэша используйте команду `/refresh_cache`.

## Обработка ошибок

Система включает fallback механизмы:

1. Если ролевая система не инициализирована, все разрешения считаются доступными
2. Если пользователь не найден, доступ блокируется
3. Если роль не назначена, доступ блокируется

## Расширение системы

### Добавление новой роли

```python
# В LarkRoleProvider._load_default_roles()
"new_role": RolePermissions(
    role_name="new_role",
    permissions={
        "can_use_analysis": True,
        "can_receive_digest": True,
        # другие разрешения...
    },
    description="Описание новой роли"
)
```

### Добавление нового разрешения

1. Добавьте разрешение в `get_available_permissions()`
2. Добавьте описание в `get_permission_description()`
3. Обновите роли, добавив новое разрешение
4. Используйте декоратор `@require_permission("new_permission")`

## Логирование

Система логирует:
- Инициализацию ролевой системы
- Ошибки при получении данных
- Проверки разрешений (в режиме отладки)

## Безопасность

- Все запросы к Lark API используют HTTPS
- Токены доступа кэшируются и обновляются автоматически
- Пользователи без роли не имеют доступа к функциям
- Система проверяет whitelist перед проверкой разрешений 