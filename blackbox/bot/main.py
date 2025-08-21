import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from logger_config import setup_logger

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логгер
logger = setup_logger("bot")

# Инициализация бота
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Глобальная переменная для ролевого менеджера
role_manager = None

async def initialize_role_system():
    """Инициализация ролевой системы"""
    logger.info("Начало инициализации ролевой системы...")
    print(f"🔍 [DEBUG] bot/main.py: initialize_role_system() вызвана")
    
    try:
        # Импортируем конфигурацию
        from config import get_role_system_config
        logger.info("Конфигурация импортирована")
        print(f"✅ [DEBUG] bot/main.py: Конфигурация импортирована")
        
        # Получаем конфигурацию
        role_config = get_role_system_config()["lark"]
        logger.info(f"Конфигурация получена: {role_config['app_id']}")
        print(f"✅ [DEBUG] bot/main.py: Конфигурация получена: {role_config['app_id']}")
        
        # Импортируем провайдеры
        from role_model.lark_provider import LarkUserProvider
        from role_model.mongodb_provider import MongoDBRoleProvider
        from role_model.role_manager import RoleManager
        logger.info("Провайдеры импортированы")
        print(f"✅ [DEBUG] bot/main.py: Провайдеры импортированы")
        
        # Создаем провайдеры
        user_provider = LarkUserProvider(
            app_id=role_config["app_id"],
            app_secret=role_config["app_secret"],
            table_app_id=role_config["table_app_id"],
            table_id=role_config["table_id"]
        )
        logger.info("LarkUserProvider создан")
        print(f"✅ [DEBUG] bot/main.py: LarkUserProvider создан")
        
        # Запускаем периодическую синхронизацию
        await user_provider.start_periodic_sync()
        logger.info("Периодическая синхронизация запущена")
        print(f"✅ [DEBUG] bot/main.py: Периодическая синхронизация запущена")
        
        # Используем MongoDB провайдер для ролей
        role_provider = MongoDBRoleProvider()
        logger.info("MongoDBRoleProvider создан")
        print(f"✅ [DEBUG] bot/main.py: MongoDBRoleProvider создан")
        
        # Создаем менеджер ролей
        role_manager = RoleManager(user_provider, role_provider)
        logger.info("RoleManager создан")
        print(f"✅ [DEBUG] bot/main.py: RoleManager создан")
        
        # Синхронизируем пользователей из Lark
        logger.info("Синхронизация пользователей из Lark...")
        print(f"🔄 [DEBUG] bot/main.py: Синхронизация пользователей из Lark...")
        try:
            users_count = await user_provider.sync_users_from_lark()
            logger.info(f"Синхронизировано {users_count} пользователей из Lark")
            print(f"✅ [DEBUG] bot/main.py: Синхронизировано {users_count} пользователей из Lark")
        except Exception as e:
            logger.error(f"Ошибка при синхронизации пользователей из Lark: {e}")
            print(f"❌ [DEBUG] bot/main.py: Ошибка при синхронизации пользователей из Lark: {e}")
            # Продолжаем инициализацию даже при ошибке синхронизации
        
        # Инициализируем роли по умолчанию
        await role_provider.ensure_default_roles()
        logger.info("Роли по умолчанию инициализированы")
        print(f"✅ [DEBUG] bot/main.py: Роли по умолчанию инициализированы")
        
        logger.info("Ролевая система успешно инициализирована с MongoDB")
        print(f"✅ [DEBUG] bot/main.py: Ролевая система успешно инициализирована с MongoDB")
        
        return role_manager
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации ролевой системы: {e}")
        print(f"❌ [DEBUG] bot/main.py: Ошибка при инициализации ролевой системы: {e}")
        return None

async def set_commands():
    """Установка команд бота"""
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="main_menu", description="Функционал бота"),
        types.BotCommand(command="permissions", description="Мои разрешения"),
        types.BotCommand(command="role_management", description="Управление ролями (админ)"),
    ]
    await bot.set_my_commands(commands)

async def main():
    """Основная функция запуска бота"""
    try:
        # Инициализируем ролевую систему
        await initialize_role_system()
        
        # Инициализируем планировщик дайджестов
        from digest_scheduler_service import get_digest_scheduler
        digest_scheduler = get_digest_scheduler(bot)
        await digest_scheduler.start_scheduler()
        
        # Импортируем хендлеры после инициализации бота
        from handlers.start_handlers import register_handlers as register_start_handlers
        from handlers.sources_handlers import register_handlers as register_sources_handlers
        from handlers.analysis_handlers import register_handlers as register_analysis_handlers
        from handlers.subscription_handlers import register_handlers as register_subscription_handlers
        from handlers.auth_handlers import register_handlers as register_auth_handlers
        from handlers.admin_handlers import register_handlers as register_admin_handlers
        from handlers.role_management_handlers import register_handlers as register_role_management_handlers
        from handlers.telegram_channels_handlers import register_handlers as register_telegram_channels_handlers
        from handlers.channel_join_handlers import register_handlers as register_channel_join_handlers
        from handlers.main_handlers import register_main_handlers

        def register_all_handlers(dp: Dispatcher):
            """Регистрация всех хендлеров"""
            register_main_handlers(dp)  # Новые хендлеры с проверкой доступа
            register_start_handlers(dp)
            register_sources_handlers(dp)
            register_analysis_handlers(dp)
            register_subscription_handlers(dp)
            register_auth_handlers(dp)
            register_admin_handlers(dp)
            register_role_management_handlers(dp)
            register_telegram_channels_handlers(dp)
            register_channel_join_handlers(dp)
        
        # Регистрируем все хендлеры
        register_all_handlers(dp)
        
        # Устанавливаем команды бота
        await set_commands()
        
        # Запускаем бота
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        raise

def get_role_manager():
    """Получить глобальный менеджер ролей"""
    return role_manager

async def get_role_manager_async():
    """Асинхронная функция для получения ролевого менеджера"""
    print(f"🔍 [DEBUG] bot/main.py: get_role_manager_async() вызвана")
    
    global role_manager
    if not role_manager:
        print(f"🔍 [DEBUG] bot/main.py: role_manager не инициализирован, инициализируем...")
        role_manager = await initialize_role_system()
        if role_manager:
            print(f"✅ [DEBUG] bot/main.py: role_manager успешно инициализирован")
        else:
            print(f"❌ [DEBUG] bot/main.py: role_manager не удалось инициализировать")
    else:
        print(f"✅ [DEBUG] bot/main.py: role_manager уже инициализирован")
    
    return role_manager

if __name__ == "__main__":
    asyncio.run(main())
