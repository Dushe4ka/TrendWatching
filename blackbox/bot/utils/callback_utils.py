import hashlib
from typing import Dict, Tuple, Any
from datetime import datetime

# Кэш для хранения хешей и их значений
_callback_cache: Dict[str, Dict[str, Any]] = {}

def create_short_callback(action: str, **kwargs) -> str:
    """
    Создает короткий callback_data с помощью MD5 хеширования
    
    Args:
        action: Действие (например, 'channel_info', 'add_digest')
        **kwargs: Параметры для callback
        
    Returns:
        str: Короткий callback_data
    """
    # Создаем уникальную строку для хеширования
    pairs = [f'{k}={v}' for k, v in sorted(kwargs.items())]
    data_str = f"{action}:{':'.join(pairs)}"
    
    # Создаем MD5 хеш (первые 16 символов)
    hash_obj = hashlib.md5(data_str.encode('utf-8'))
    short_hash = hash_obj.hexdigest()[:16]
    
    # Сохраняем в кэш
    _callback_cache[short_hash] = {
        'action': action,
        'data': kwargs,
        'timestamp': datetime.utcnow()
    }
    
    return short_hash

def parse_short_callback(callback_data: str) -> Tuple[str, Dict[str, Any]]:
    """
    Парсит короткий callback_data и возвращает действие и данные
    
    Args:
        callback_data: Короткий callback_data
        
    Returns:
        Tuple[str, Dict[str, Any]]: (действие, данные)
        
    Raises:
        ValueError: Если callback_data не найден в кэше
    """
    if callback_data not in _callback_cache:
        raise ValueError(f"Callback data не найден: {callback_data}")
    
    cached_data = _callback_cache[callback_data]
    print(f"🔍 DEBUG: parse_short_callback - callback_data={callback_data}, cached_data={cached_data}")
    
    return cached_data['action'], cached_data['data']

def cleanup_old_callbacks(max_age_hours: int = 24):
    """
    Очищает старые callback_data из кэша
    
    Args:
        max_age_hours: Максимальный возраст в часах
    """
    current_time = datetime.utcnow()
    keys_to_remove = []
    
    for key, data in _callback_cache.items():
        age = current_time - data['timestamp']
        if age.total_seconds() > max_age_hours * 3600:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del _callback_cache[key]

# Специальные функции для конкретных действий
def create_channel_callback(action: str, channel_id: int) -> str:
    """Создает callback для действий с каналом"""
    return create_short_callback(action, channel_id=channel_id)

def create_digest_callback(action: str, channel_id: int, digest_id: str = None, **kwargs) -> str:
    """Создает callback для действий с дайджестом"""
    print(f"🔍 DEBUG: create_digest_callback - входные параметры: action={action}, channel_id={channel_id}, digest_id={digest_id}, kwargs={kwargs}")
    
    data = {'channel_id': channel_id}
    if digest_id:
        data['digest_id'] = digest_id
    
    # Добавляем дополнительные параметры
    for key, value in kwargs.items():
        data[key] = value
    
    print(f"🔍 DEBUG: create_digest_callback - итоговые данные: data={data}")
    
    return create_short_callback(action, **data)

def create_category_callback(action: str, channel_id: int, category: str) -> str:
    """Создает callback для действий с категорией"""
    return create_short_callback(action, channel_id=channel_id, category=category) 