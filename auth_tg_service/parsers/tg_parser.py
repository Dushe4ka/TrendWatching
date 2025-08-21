from telethon import TelegramClient
import logging
import re
import asyncio
from .utils import decode_if_bytes, save_parsed_data
from config import API_ID, API_HASH
from session_manager import get_session_file_path

log = logging.getLogger(__name__)

def extract_channel_username(url):
    """Извлекает username канала из URL"""
    # Убираем https://t.me/ или @ если они есть
    username = re.sub(r'^https?://t\.me/', '', url)
    username = re.sub(r'^@', '', username)
    return username

async def parse_tg_channel_with_session(channel: str, category: str, phone_number: str, 
                                      api_id: int, api_hash: str, parsed_data_collection, 
                                      limit: int = 50):
    """
    Парсит Telegram канал используя конкретную сессию
    
    Args:
        channel: URL или username канала
        category: Категория для спарсенных данных
        phone_number: Номер телефона сессии
        api_id: API ID для Telegram
        api_hash: API Hash для Telegram
        parsed_data_collection: MongoDB коллекция для сохранения данных
        limit: Лимит сообщений для парсинга
    
    Returns:
        int: Количество спарсенных записей или None при ошибке
    """
    log.info(f"Начало парсинга Telegram-канала {channel} с сессией {phone_number}")
    
    try:
        # Извлекаем username из URL
        channel_username = extract_channel_username(channel)
        if not channel_username:
            log.error(f"❌ Не удалось извлечь username из {channel}")
            return None
        
        log.info(f"Извлечен username канала: {channel_username}")
        
        # Используем существующий файл сессии
        session_file = get_session_file_path(phone_number)
        client = TelegramClient(session_file, api_id, api_hash)
        
        try:
            await client.connect()
            
            # Проверяем авторизацию
            is_authorized = await client.is_user_authorized()
            if not is_authorized:
                log.error(f"❌ Сессия {phone_number} не авторизована. Пропускаем.")
                return None

            if await client.is_bot():
                log.error(f"❌ Сессия {phone_number} - бот. Боты не могут парсить каналы.")
                return None

            saved_count = 0
            async for message in client.iter_messages(channel_username, limit=limit):
                if message.text:
                    text = decode_if_bytes(message.text)
                    data = {
                        "url": f"https://t.me/{channel_username}/{message.id}",
                        "title": text[:100] if text else "",
                        "description": text,
                        "content": text,
                        "date": message.date,
                        "category": category,
                        "source_type": "telegram",
                        "source_url": channel,
                        "session_phone": phone_number
                    }
                    
                    if await save_parsed_data(data, parsed_data_collection):
                        saved_count += 1
                        print(f"📱 TG ({phone_number}): {text[:100]}... | https://t.me/{channel_username}/{message.id}")
            
            log.info(f"✅ Успешно спаршено {saved_count} постов из {channel_username} с сессией {phone_number}")
            return saved_count
            
        except Exception as e:
            log.error(f"❌ Ошибка при парсинге канала {channel} с сессией {phone_number}: {str(e)}")
            return None
        finally:
            try:
                await client.disconnect()
                log.info(f"🔌 Отключение от Telegram для {phone_number}")
            except Exception as disconnect_error:
                log.warning(f"⚠️ Ошибка при disconnect: {disconnect_error}")
            
    except Exception as e:
        log.error(f"❌ Ошибка при парсинге Telegram ({channel}): {str(e)}")
        return None

async def parse_tg_channel_distributed(channel: str, category: str, sessions: list, 
                                     parsed_data_collection, limit: int = 50):
    """
    Парсит Telegram канал используя распределение по сессиям
    
    Args:
        channel: URL или username канала
        category: Категория для спарсенных данных
        sessions: Список сессий для использования
        parsed_data_collection: MongoDB коллекция для сохранения данных
        limit: Лимит сообщений для парсинга
    
    Returns:
        dict: Результаты парсинга по сессиям
    """
    log.info(f"Начало распределенного парсинга Telegram-канала: {channel}")
    
    results = {}
    tasks = []
    
    # Создаем задачи для каждой сессии
    for session in sessions:
        phone_number = session.get('phone_number')
        if not phone_number:
            continue
            
        task = parse_tg_channel_with_session(
            channel=channel,
            category=category,
            phone_number=phone_number,
            api_id=API_ID,
            api_hash=API_HASH,
            parsed_data_collection=parsed_data_collection,
            limit=limit
        )
        tasks.append((phone_number, task))
    
    # Выполняем задачи параллельно
    if tasks:
        phone_numbers, coroutines = zip(*tasks)
        results_list = await asyncio.gather(*coroutines, return_exceptions=True)
        
        for phone_number, result in zip(phone_numbers, results_list):
            if isinstance(result, Exception):
                log.error(f"❌ Ошибка в сессии {phone_number}: {result}")
                results[phone_number] = None
            else:
                results[phone_number] = result
    
    total_saved = sum(r for r in results.values() if r is not None)
    log.info(f"✅ Распределенный парсинг завершен. Всего спаршено: {total_saved}")
    
    return results
