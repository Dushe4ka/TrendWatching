import re
from typing import List, Tuple
from logger_config import setup_logger

# Настраиваем логгер
logger = setup_logger("message_utils")

# Константы для Telegram
MAX_MESSAGE_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024
# Резерв для дополнительных вставок (заголовки продолжения, номера частей и т.д.)
# Учитываем максимальную длину суффикса "--- Часть 999 из 999 ---" = ~30 символов + запас
SAFETY_MARGIN = 250

def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> List[str]:
    """
    Разбивает длинное сообщение на части, сохраняя целостность предложений
    
    Args:
        text: Текст для разбиения
        max_length: Максимальная длина одной части (по умолчанию 4096 для Telegram)
    
    Returns:
        Список частей сообщения
    """
    # Используем безопасный запас для учета дополнительных вставок
    safe_max_length = max_length - SAFETY_MARGIN
    
    logger.debug(f"Разбиение сообщения: длина текста={len(text)}, max_length={max_length}, safe_max_length={safe_max_length}")
    
    if len(text) <= safe_max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    # Разбиваем текст на предложения
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Если нет предложений или только одно предложение, разбиваем по словам
    if len(sentences) <= 1:
        words = text.split()
        
        # Если нет слов (например, только символы без пробелов), разбиваем по символам
        if len(words) <= 1:
            # Разбиваем текст на части по safe_max_length символов
            for i in range(0, len(text), safe_max_length):
                part = text[i:i + safe_max_length]
                if part:
                    parts.append(part)
            return parts
        
        # Разбиваем по словам
        current_part = ""
        
        for word in words:
            if len(current_part + " " + word) <= safe_max_length:
                current_part += (" " + word) if current_part else word
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = word
        
        if current_part:
            parts.append(current_part.strip())
        
        return parts
    
    # Обрабатываем предложения
    for sentence in sentences:
        # Если предложение само по себе длиннее лимита
        if len(sentence) > safe_max_length:
            # Если у нас есть накопленный текст, сохраняем его
            if current_part:
                parts.append(current_part.strip())
                current_part = ""
            
            # Разбиваем длинное предложение по словам
            words = sentence.split()
            temp_part = ""
            
            for word in words:
                if len(temp_part + " " + word) <= safe_max_length:
                    temp_part += (" " + word) if temp_part else word
                else:
                    if temp_part:
                        parts.append(temp_part.strip())
                    temp_part = word
            
            if temp_part:
                current_part = temp_part
        else:
            # Проверяем, поместится ли предложение в текущую часть
            if len(current_part + " " + sentence) <= safe_max_length:
                current_part += (" " + sentence) if current_part else sentence
            else:
                # Сохраняем текущую часть и начинаем новую
                if current_part:
                    parts.append(current_part.strip())
                current_part = sentence
    
    # Добавляем последнюю часть
    if current_part:
        parts.append(current_part.strip())
    
    logger.debug(f"Сообщение разбито на {len(parts)} частей. Длины частей: {[len(part) for part in parts]}")
    
    return parts

def split_analysis_message(
    analysis_text: str,
    materials_count: int,
    category: str = None,
    date: str = None,
    analysis_type: str = None
) -> List[str]:
    """
    Специальная функция для разбиения сообщений анализа новостей
    
    Args:
        analysis_text: Текст анализа
        materials_count: Количество проанализированных материалов
        category: Категория анализа (опционально)
        date: Дата анализа (опционально)
        analysis_type: Тип анализа ("daily", "weekly", "trend_query", "single_day")
    
    Returns:
        Список частей сообщения
    """
    # Формируем заголовок в зависимости от типа анализа
    if analysis_type == "weekly":
        header = "✅ Анализ новостей за неделю завершен!\n\n"
    elif analysis_type == "single_day":
        header = "✅ Анализ новостей за сутки завершен!\n\n"
    elif analysis_type == "trend_query":
        header = "✅ Анализ тренда по запросу завершен!\n\n"
    else:
        header = "✅ Анализ новостей завершен!\n\n"
    if category:
        header += f"📂 Категория: {category}\n"
    if date:
        header += f"📅 Дата: {date}\n"
    header += f"📊 Проанализировано материалов: {materials_count}\n\n"
    
    # Если весь текст помещается в одно сообщение
    full_message = header + f"📝 Результаты анализа:\n{analysis_text}"
    logger.debug(f"Анализ: длина полного сообщения={len(full_message)}, лимит={MAX_MESSAGE_LENGTH - SAFETY_MARGIN}")
    if len(full_message) <= MAX_MESSAGE_LENGTH - SAFETY_MARGIN:
        return [full_message]
    
    # Разбиваем на части
    parts = []
    
    # Первая часть с заголовком
    first_part = header + "📝 Результаты анализа:\n"
    remaining_length = MAX_MESSAGE_LENGTH - len(first_part) - SAFETY_MARGIN
    
    # Находим подходящее место для разрыва в анализе
    analysis_parts = split_message(analysis_text, remaining_length)
    
    if analysis_parts:
        first_part += analysis_parts[0]
        parts.append(first_part)
        
        # Добавляем остальные части анализа
        for i, part in enumerate(analysis_parts[1:], 2):
            continuation_header = f"📝 Продолжение анализа (часть {i}):\n"
            # Учитываем длину заголовка продолжения при разбиении
            continuation_remaining = MAX_MESSAGE_LENGTH - len(continuation_header) - SAFETY_MARGIN
            continuation_parts = split_message(part, continuation_remaining)
            
            for j, continuation_part in enumerate(continuation_parts):
                if j == 0:
                    parts.append(continuation_header + continuation_part)
                else:
                    parts.append(f"📝 Продолжение анализа (часть {i}.{j+1}):\n{continuation_part}")
    
    logger.debug(f"Анализ разбит на {len(parts)} частей. Длины частей: {[len(part) for part in parts]}")
    return parts

def split_digest_message(digest_text: str, date: str, total_materials: int) -> List[str]:
    """
    Специальная функция для разбиения дайджеста новостей
    
    Args:
        digest_text: Текст дайджеста
        date: Дата дайджеста
        total_materials: Общее количество материалов
    
    Returns:
        Список частей сообщения
    """
    # Формируем заголовок
    header = f"📰 Ежедневный дайджест новостей за {date}\n\n"
    header += f"📊 Всего проанализировано материалов: {total_materials}\n\n"
    
    # Если весь текст помещается в одно сообщение
    full_message = header + digest_text
    logger.debug(f"Дайджест: длина полного сообщения={len(full_message)}, лимит={MAX_MESSAGE_LENGTH - SAFETY_MARGIN}")
    if len(full_message) <= MAX_MESSAGE_LENGTH - SAFETY_MARGIN:
        return [full_message]
    
    # Разбиваем на части
    parts = []
    
    # Первая часть с заголовком
    first_part = header
    remaining_length = MAX_MESSAGE_LENGTH - len(first_part) - SAFETY_MARGIN
    
    # Находим подходящее место для разрыва в дайджесте
    digest_parts = split_message(digest_text, remaining_length)
    
    if digest_parts:
        first_part += digest_parts[0]
        parts.append(first_part)
        
        # Добавляем остальные части дайджеста
        for i, part in enumerate(digest_parts[1:], 2):
            continuation_header = f"📰 Продолжение дайджеста (часть {i}):\n"
            # Учитываем длину заголовка продолжения при разбиении
            continuation_remaining = MAX_MESSAGE_LENGTH - len(continuation_header) - SAFETY_MARGIN
            continuation_parts = split_message(part, continuation_remaining)
            
            for j, continuation_part in enumerate(continuation_parts):
                if j == 0:
                    parts.append(continuation_header + continuation_part)
                else:
                    parts.append(f"📰 Продолжение дайджеста (часть {i}.{j+1}):\n{continuation_part}")
    
    logger.debug(f"Дайджест разбит на {len(parts)} частей. Длины частей: {[len(part) for part in parts]}")
    return parts

def format_message_part(part: str, part_number: int = None, total_parts: int = None) -> str:
    """
    Форматирует часть сообщения с указанием номера части
    
    Args:
        part: Текст части сообщения
        part_number: Номер части (начиная с 1)
        total_parts: Общее количество частей
    
    Returns:
        Отформатированная часть сообщения
    """
    if part_number and total_parts and total_parts > 1:
        suffix = f"\n\n--- Часть {part_number} из {total_parts} ---"
        # Проверяем, не превышает ли итоговое сообщение лимит
        if len(part) + len(suffix) > MAX_MESSAGE_LENGTH:
            logger.warning(f"Часть {part_number} из {total_parts} превышает лимит: {len(part) + len(suffix)} > {MAX_MESSAGE_LENGTH}")
            # Если превышает, убираем суффикс
            return part
        return f"{part}{suffix}"
    return part 