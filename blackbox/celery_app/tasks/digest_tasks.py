from celery_app import app
from usecases.daily_news import analyze_trend
from aiogram import Bot
import os
from dotenv import load_dotenv
import asyncio
import time
from celery import current_task
from datetime import datetime, timedelta
from telegram_channels_service import telegram_channels_service
from utils.message_utils import split_analysis_message, format_message_part
from logger_config import setup_logger
import warnings
from celery.schedules import crontab
import json

# Игнорируем предупреждения о MongoDB и fork
warnings.filterwarnings("ignore", message="MongoClient opened before fork")

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логгер
logger = setup_logger("digest_tasks")

async def send_digest_to_channel(bot, channel_id: int, message_parts: list):
    """Отправка дайджеста в Telegram канал"""
    try:
        for i, part in enumerate(message_parts, 1):
            formatted_part = format_message_part(part, i, len(message_parts))
            await bot.send_message(chat_id=channel_id, text=formatted_part, parse_mode="HTML")
            if i < len(message_parts):
                await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями
        logger.info(f"Дайджест успешно отправлен в канал {channel_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки дайджеста в канал {channel_id}: {str(e)}")
        raise
    finally:
        await bot.session.close()

@app.task(bind=True, name='celery_app.tasks.digest_tasks.send_telegram_digest')
def send_telegram_digest(self, channel_id: int, digest_id: str, category: str) -> dict:
    """
    Отложенная задача для отправки дайджеста в Telegram канал
    
    Args:
        channel_id: ID Telegram канала
        digest_id: ID дайджеста
        category: Категория для анализа
    """
    start_time = time.time()
    worker_id = current_task.request.hostname
    process_id = os.getpid()
    worker_num = process_id % 5 + 1  # Номер воркера (1-5)
    
    logger.info(f"=== Воркер {worker_num} (PID: {process_id}) начал отправку дайджеста ===")
    logger.info(f"Канал: {channel_id}")
    logger.info(f"Дайджест: {digest_id}")
    logger.info(f"Категория: {category}")
    
    try:
        # Получаем информацию о канале
        channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        if not channel_info:
            error_msg = f"Канал {channel_id} не найден"
            logger.error(error_msg)
            return {'status': 'error', 'message': error_msg}
        
        # Находим дайджест
        digest = None
        for d in channel_info.digests:
            if d.id == digest_id:
                digest = d
                break
        
        if not digest:
            # Если дайджест не найден, но это тестовый дайджест, продолжаем
            if digest_id.startswith('test_'):
                logger.info(f"Тестовый дайджест {digest_id} - пропускаем проверку существования")
                # Создаем временный объект дайджеста для теста
                class TempDigest:
                    def __init__(self, time_str):
                        self.time = time_str
                        self.is_active = True
                
                digest = TempDigest("ТЕСТ")
            else:
                error_msg = f"Дайджест {digest_id} не найден в канале {channel_id}"
                logger.error(error_msg)
                return {'status': 'error', 'message': error_msg}
        
        if not digest.is_active:
            logger.info(f"Дайджест {digest_id} неактивен, пропускаем")
            return {'status': 'skipped', 'message': 'Дайджест неактивен'}
        
        # Выполняем анализ новостей для категории
        today = datetime.now().strftime('%Y-%m-%d')
        result = analyze_trend(
            category=category,
            analysis_date=today
        )
        
        if result['status'] == 'success':
            # Форматируем дайджест
            message_parts = split_analysis_message(
                analysis_text=result['analysis'],
                materials_count=result['materials_count'],
                category=category,
                date=today,
                analysis_type='daily_digest'
            )
            
            # Добавляем заголовок дайджеста
            header = f"📰 <b>Ежедневный дайджест</b>\n\n"
            header += f"📢 Канал: {channel_info.channel.title}\n"
            header += f"🏷️ Категория: {category}\n"
            header += f"📅 Дата: {today}\n"
            header += f"⏰ Время отправки: {digest.time}\n\n"
            
            # Добавляем заголовок к первому сообщению
            if message_parts:
                message_parts[0] = header + message_parts[0]
            
            # Отправляем дайджест в канал
            bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
            asyncio.run(send_digest_to_channel(bot, channel_id, message_parts))
            
            execution_time = time.time() - start_time
            logger.info(f"=== Воркер {worker_num} (PID: {process_id}) завершил отправку дайджеста за {execution_time:.2f} секунд ===")
            
            return {
                'status': 'success',
                'channel_id': channel_id,
                'digest_id': digest_id,
                'category': category,
                'parts_count': len(message_parts),
                'message': 'Дайджест успешно отправлен'
            }
        else:
            error_message = f"❌ Ошибка при анализе новостей: {result['message']}"
            logger.error(error_message)
            
            # Отправляем сообщение об ошибке в канал
            try:
                bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
                error_text = f"❌ <b>Ошибка отправки дайджеста</b>\n\nКатегория: {category}\nОшибка: {result['message']}"
                asyncio.run(bot.send_message(chat_id=channel_id, text=error_text, parse_mode="HTML"))
                asyncio.run(bot.session.close())
            except Exception as bot_error:
                logger.error(f"Не удалось отправить сообщение об ошибке: {str(bot_error)}")
            
            return {
                'status': 'error',
                'channel_id': channel_id,
                'digest_id': digest_id,
                'message': error_message
            }
            
    except Exception as e:
        error_message = f"❌ Произошла ошибка при отправке дайджеста: {str(e)}"
        logger.error(error_message)
        
        # Отправляем ошибку в канал
        try:
            bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
            error_text = f"❌ <b>Ошибка отправки дайджеста</b>\n\nКатегория: {category}\nОшибка: {str(e)}"
            asyncio.run(bot.send_message(chat_id=channel_id, text=error_text, parse_mode="HTML"))
            asyncio.run(bot.session.close())
        except Exception as bot_error:
            logger.error(f"Не удалось отправить сообщение об ошибке: {str(bot_error)}")
        
        return {
            'status': 'error',
            'channel_id': channel_id,
            'digest_id': digest_id,
            'message': error_message
        }

@app.task(bind=True, name='celery_app.tasks.digest_tasks.send_test_digest')
def send_test_digest(self, channel_id: int, category: str = "Видеоигры") -> dict:
    """
    Тестовая задача для отправки дайджеста (для проверки работы)
    
    Args:
        channel_id: ID Telegram канала
        category: Категория для анализа
    """
    start_time = time.time()
    worker_id = current_task.request.hostname
    process_id = os.getpid()
    worker_num = process_id % 5 + 1
    
    logger.info(f"=== Воркер {worker_num} (PID: {process_id}) начал отправку тестового дайджеста ===")
    logger.info(f"Канал: {channel_id}")
    logger.info(f"Категория: {category}")
    
    try:
        # Получаем информацию о канале
        channel_info = telegram_channels_service.get_channel_by_id(channel_id)
        if not channel_info:
            error_msg = f"Канал {channel_id} не найден"
            logger.error(error_msg)
            return {'status': 'error', 'message': error_msg}
        
        # Выполняем анализ новостей для категории
        today = datetime.now().strftime('%Y-%m-%d')
        result = analyze_trend(
            category=category,
            analysis_date=today
        )
        
        if result['status'] == 'success':
            # Форматируем дайджест
            message_parts = split_analysis_message(
                analysis_text=result['analysis'],
                materials_count=result['materials_count'],
                category=category,
                date=today,
                analysis_type='daily_digest'
            )
            
            # Добавляем заголовок тестового дайджеста
            header = f"🧪 <b>ТЕСТОВЫЙ дайджест</b>\n\n"
            header += f"📢 Канал: {channel_info.channel.title}\n"
            header += f"🏷️ Категория: {category}\n"
            header += f"📅 Дата: {today}\n"
            header += f"⏰ Время отправки: ТЕСТ\n\n"
            
            # Добавляем заголовок к первому сообщению
            if message_parts:
                message_parts[0] = header + message_parts[0]
            
            # Отправляем дайджест в канал
            bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
            asyncio.run(send_digest_to_channel(bot, channel_id, message_parts))
            
            execution_time = time.time() - start_time
            logger.info(f"=== Воркер {worker_num} (PID: {process_id}) завершил отправку тестового дайджеста за {execution_time:.2f} секунд ===")
            
            return {
                'status': 'success',
                'channel_id': channel_id,
                'category': category,
                'parts_count': len(message_parts),
                'message': 'Тестовый дайджест успешно отправлен'
            }
        else:
            error_message = f"❌ Ошибка при анализе новостей: {result['message']}"
            logger.error(error_message)
            
            # Отправляем сообщение об ошибке в канал
            try:
                bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
                error_text = f"❌ <b>Ошибка отправки тестового дайджеста</b>\n\nКатегория: {category}\nОшибка: {result['message']}"
                asyncio.run(bot.send_message(chat_id=channel_id, text=error_text, parse_mode="HTML"))
                asyncio.run(bot.session.close())
            except Exception as bot_error:
                logger.error(f"Не удалось отправить сообщение об ошибке: {str(bot_error)}")
            
            return {
                'status': 'error',
                'channel_id': channel_id,
                'message': error_message
            }
            
    except Exception as e:
        error_message = f"❌ Произошла ошибка при отправке тестового дайджеста: {str(e)}"
        logger.error(error_message)
        
        # Отправляем ошибку в канал
        try:
            bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
            error_text = f"❌ <b>Ошибка отправки тестового дайджеста</b>\n\nКатегория: {category}\nОшибка: {str(e)}"
            asyncio.run(bot.send_message(chat_id=channel_id, text=error_text, parse_mode="HTML"))
            asyncio.run(bot.session.close())
        except Exception as bot_error:
            logger.error(f"Не удалось отправить сообщение об ошибке: {str(bot_error)}")
        
        return {
            'status': 'error',
            'channel_id': channel_id,
            'message': error_message
        } 