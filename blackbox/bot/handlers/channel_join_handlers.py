from aiogram import Dispatcher, types
from telegram_channels_service import telegram_channels_service
from logger_config import setup_logger

# Настраиваем логгер
logger = setup_logger("channel_join_handlers")

async def handle_chat_member_update(chat_member_update: types.ChatMemberUpdated):
    """
    Обработчик обновления участников чата
    Автоматически сохраняет информацию о каналах, куда добавлен бот
    """
    try:
        # Проверяем, что это обновление статуса бота
        if chat_member_update.new_chat_member.user.id == chat_member_update.bot.id:
            # Получаем информацию о чате
            chat = chat_member_update.chat
            
            # Проверяем, что это канал или супергруппа
            if chat.type in ["channel", "supergroup"]:
                # Проверяем, что бот стал администратором
                if chat_member_update.new_chat_member.status in ["administrator", "creator"]:
                    logger.info(f"Бот добавлен как администратор в канал: {chat.title} (ID: {chat.id})")
                    
                    # Сохраняем информацию о канале
                    channel_data = {
                        "id": chat.id,
                        "title": chat.title,
                        "username": chat.username,
                        "type": chat.type
                    }
                    
                    success = telegram_channels_service.add_channel(channel_data)
                    if success:
                        logger.info(f"Канал {chat.title} успешно сохранен в базе данных")
                    else:
                        logger.error(f"Ошибка при сохранении канала {chat.title}")
                
                elif chat_member_update.new_chat_member.status in ["left", "kicked"]:
                    logger.info(f"Бот удален из канала: {chat.title} (ID: {chat.id})")
                    # Здесь можно добавить логику для деактивации дайджестов
                    
    except Exception as e:
        logger.error(f"Ошибка при обработке обновления участников чата: {str(e)}")

async def handle_my_chat_member_update(chat_member_update: types.ChatMemberUpdated):
    """
    Обработчик обновления статуса бота в чате
    Более надежный способ отслеживания изменений статуса бота
    """
    try:
        # Получаем информацию о чате
        chat = chat_member_update.chat
        
        # Проверяем, что это канал или супергруппа
        if chat.type in ["channel", "supergroup"]:
            new_status = chat_member_update.new_chat_member.status
            old_status = chat_member_update.old_chat_member.status if chat_member_update.old_chat_member else None
            
            logger.info(f"Статус бота в канале {chat.title} изменился: {old_status} -> {new_status}")
            
            # Если бот стал администратором
            if new_status in ["administrator", "creator"]:
                logger.info(f"Бот добавлен как администратор в канал: {chat.title} (ID: {chat.id})")
                
                # Сохраняем информацию о канале
                channel_data = {
                    "id": chat.id,
                    "title": chat.title,
                    "username": chat.username,
                    "type": chat.type
                }
                
                success = telegram_channels_service.add_channel(channel_data)
                if success:
                    logger.info(f"Канал {chat.title} успешно сохранен в базе данных")
                else:
                    logger.error(f"Ошибка при сохранении канала {chat.title}")
            
            # Если бот был удален
            elif new_status in ["left", "kicked"]:
                logger.info(f"Бот удален из канала: {chat.title} (ID: {chat.id})")
                # Здесь можно добавить логику для деактивации дайджестов
                
    except Exception as e:
        logger.error(f"Ошибка при обработке обновления статуса бота: {str(e)}")

def register_handlers(dp: Dispatcher):
    """Регистрация хендлеров для автоматического добавления в каналы"""
    # Регистрируем обработчики обновлений участников чата
    dp.chat_member.register(handle_chat_member_update)
    dp.my_chat_member.register(handle_my_chat_member_update) 