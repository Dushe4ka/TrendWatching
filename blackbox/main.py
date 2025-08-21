import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from logger_config import setup_logger

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логгер
logger = setup_logger("main")

# Инициализация бота
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Глобальная переменная для ролевого менеджера
role_manager = None
_role_system_initialized = False

async def initialize_role_system():
    """Инициализация ролевой системы"""
    logger.info("Начало инициализации ролевой системы...")
    print(f"🔍 [DEBUG] main.py: initialize_role_system() вызвана")
    
    try:
        # Импортируем конфигурацию
        from config import get_role_system_config
        logger.info("Конфигурация импортирована")
        print(f"✅ [DEBUG] main.py: Конфигурация импортирована")
        
        # Получаем конфигурацию
        role_config = get_role_system_config()
        logger.info(f"Конфигурация получена: {role_config['lark']['app_id']}")
        print(f"✅ [DEBUG] main.py: Конфигурация получена: {role_config['lark']['app_id']}")
        
        # Импортируем провайдеры
        from role_model.lark_provider import LarkUserProvider
        from role_model.mongodb_provider import MongoDBRoleProvider
        from role_model.role_manager import RoleManager
        logger.info("Провайдеры импортированы")
        print(f"✅ [DEBUG] main.py: Провайдеры импортированы")
        
        # Создаем провайдеры
        lark_config = role_config["lark"]
        user_provider = LarkUserProvider(
            app_id=lark_config["app_id"],
            app_secret=lark_config["app_secret"],
            table_app_id=lark_config["table_app_id"],
            table_id=lark_config["table_id"]
        )
        logger.info("LarkUserProvider создан")
        print(f"✅ [DEBUG] main.py: LarkUserProvider создан")
        
        # Запускаем периодическую синхронизацию
        await user_provider.start_periodic_sync()
        logger.info("Периодическая синхронизация запущена")
        print(f"✅ [DEBUG] main.py: Периодическая синхронизация запущена")
        
        # Используем MongoDB провайдер для ролей
        role_provider = MongoDBRoleProvider()
        logger.info("MongoDBRoleProvider создан")
        print(f"✅ [DEBUG] main.py: MongoDBRoleProvider создан")
        
        # Создаем менеджер ролей
        role_manager = RoleManager(user_provider, role_provider)
        logger.info("RoleManager создан")
        print(f"✅ [DEBUG] main.py: RoleManager создан")
        
        # Синхронизируем пользователей из Lark
        logger.info("Синхронизация пользователей из Lark...")
        print(f"🔄 [DEBUG] main.py: Синхронизация пользователей из Lark...")
        try:
            users_count = await user_provider.sync_users_from_lark()
            logger.info(f"Синхронизировано {users_count} пользователей из Lark")
            print(f"✅ [DEBUG] main.py: Синхронизировано {users_count} пользователей из Lark")
        except Exception as e:
            logger.error(f"Ошибка при синхронизации пользователей из Lark: {e}")
            print(f"❌ [DEBUG] main.py: Ошибка при синхронизации пользователей из Lark: {e}")
            # Продолжаем инициализацию даже при ошибке синхронизации
        
        # Инициализируем роли по умолчанию
        await role_provider.ensure_default_roles()
        logger.info("Роли по умолчанию инициализированы")
        print(f"✅ [DEBUG] main.py: Роли по умолчанию инициализированы")
        
        logger.info("Ролевая система успешно инициализирована с MongoDB")
        print(f"✅ [DEBUG] main.py: Ролевая система успешно инициализирована с MongoDB")
        
        return role_manager
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации ролевой системы: {e}")
        print(f"❌ [DEBUG] main.py: Ошибка при инициализации ролевой системы: {e}")
        return None

async def set_commands():
    """Установка команд бота"""
    from aiogram import types
    commands = [
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="main_menu", description="Функционал бота"),
    ]
    await bot.set_my_commands(commands)

def get_role_manager():
    """Получить глобальный менеджер ролей"""
    global role_manager, _role_system_initialized
    
    if not _role_system_initialized or role_manager is None:
        logger.warning("⚠️ Попытка получить role_manager, но он не инициализирован")
        return None
    
    return role_manager

async def get_role_manager_async():
    """Асинхронная функция для получения ролевого менеджера"""
    print(f"🔍 [DEBUG] main.py: get_role_manager_async() вызвана")
    
    global role_manager
    if not role_manager:
        print(f"🔍 [DEBUG] main.py: role_manager не инициализирован, инициализируем...")
        role_manager = await initialize_role_system()
        if role_manager:
            print(f"✅ [DEBUG] main.py: role_manager успешно инициализирован")
        else:
            print(f"❌ [DEBUG] main.py: role_manager не удалось инициализировать")
    else:
        print(f"✅ [DEBUG] main.py: role_manager уже инициализирован")
    
    return role_manager

async def main():
    """Основная функция запуска бота"""
    try:
        # Инициализируем ролевую систему
        logger.info("Инициализация ролевой системы...")
        role_manager_instance = await initialize_role_system()
        if role_manager_instance:
            logger.info("✅ Ролевая система успешно инициализирована")
        else:
            logger.warning("⚠️ Ролевая система не инициализирована, некоторые функции могут быть недоступны")

        # --- Автоматическая инициализация APScheduler после БД ---
        from bot.apscheduler_digest import start_scheduler, init_digest_jobs_from_db
        from telegram_channels_service import telegram_channels_service
        start_scheduler()
        active_digests = telegram_channels_service.get_active_digests()
        await init_digest_jobs_from_db(active_digests)
        # ---

        # Импортируем хендлеры после инициализации бота
        from bot.handlers import (
            start_handlers,
            sources_handlers,
            analysis_handlers,
            subscription_handlers,
            auth_handlers,
            admin_handlers,
            role_management_handlers
        )
        
        # Регистрируем все хендлеры
        start_handlers.register_handlers(dp)
        sources_handlers.register_handlers(dp)
        analysis_handlers.register_handlers(dp)
        subscription_handlers.register_handlers(dp)
        auth_handlers.register_handlers(dp)
        admin_handlers.register_handlers(dp)
        role_management_handlers.register_handlers(dp)
        
        # Устанавливаем команды бота
        await set_commands()
        
        # Запускаем бота
        logger.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())