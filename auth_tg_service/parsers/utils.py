import asyncio
import logging
from hashlib import md5
from datetime import datetime

log = logging.getLogger(__name__)

def generate_hash(text: str) -> str:
    """Генерирует MD5 хеш для текста"""
    return md5(text.encode('utf-8')).hexdigest()

async def is_duplicate(url: str, parsed_data_collection) -> bool:
    """Проверяет, есть ли запись с таким url в БД"""
    try:
        count = await parsed_data_collection.count_documents({"url": url})
        is_dup = count > 0
        if is_dup:
            log.warning(f"Дубликат обнаружен по url: {url}")
        else:
            log.info(f"Успешно загружено: {url}")
        return is_dup
    except Exception as e:
        log.error(f"Ошибка при проверке дубликата: {e}")
        return False

async def retry_on_failure(func, *args, max_retries=3, delay=1, **kwargs):
    """
    Выполняет функцию с повторными попытками при сбоях
    
    Args:
        func: Асинхронная функция для выполнения
        *args: Аргументы функции
        max_retries: Максимальное количество попыток
        delay: Задержка между попытками в секундах
        **kwargs: Именованные аргументы функции
    
    Returns:
        Результат выполнения функции
        
    Raises:
        Exception: Если все попытки не удались
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                log.warning(f"Попытка {attempt + 1} не удалась: {str(e)}. Повторная попытка через {delay} сек...")
                await asyncio.sleep(delay)
            else:
                log.error(f"Все {max_retries} попыток не удались. Последняя ошибка: {str(e)}")
                raise last_error

def decode_if_bytes(value):
    """Декодирует байты в строку"""
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return value.decode('cp1251')
    return value

async def save_parsed_data(data: dict, parsed_data_collection):
    """Сохраняет спарсенные данные в MongoDB"""
    try:
        # Проверяем дубликат
        if await is_duplicate(data['url'], parsed_data_collection):
            return False
        
        # Добавляем метаданные
        data['created_at'] = datetime.utcnow()
        data['vectorized'] = False
        data['hash'] = generate_hash(data['url'] + data.get('title', ''))
        
        # Сохраняем в БД
        await parsed_data_collection.insert_one(data)
        log.info(f"Данные сохранены: {data.get('title', '')[:50]}...")
        return True
    except Exception as e:
        log.error(f"Ошибка при сохранении данных: {str(e)}")
        return False