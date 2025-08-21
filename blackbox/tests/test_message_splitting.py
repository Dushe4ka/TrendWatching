#!/usr/bin/env python3
"""
Тест функциональности разбиения сообщений
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.message_utils import split_message, split_analysis_message, split_digest_message, format_message_part

def test_split_message():
    """Тест базовой функции разбиения сообщений"""
    print("=== Тест базовой функции разбиения сообщений ===")
    
    # Короткое сообщение
    short_text = "Это короткое сообщение."
    parts = split_message(short_text)
    print(f"Короткое сообщение: {len(parts)} частей")
    assert len(parts) == 1, "Короткое сообщение должно остаться одним куском"
    
    # Длинное сообщение
    long_text = "Это очень длинное сообщение. " * 200  # Примерно 4000 символов
    parts = split_message(long_text)
    print(f"Длинное сообщение: {len(parts)} частей")
    assert len(parts) > 1, "Длинное сообщение должно быть разбито на части"
    
    # Проверяем, что каждая часть не превышает лимит
    for i, part in enumerate(parts):
        assert len(part) <= 4096, f"Часть {i+1} превышает лимит: {len(part)} символов"
        print(f"Часть {i+1}: {len(part)} символов")
    
    print("✅ Базовый тест пройден\n")

def test_split_analysis_message():
    """Тест разбиения сообщений анализа"""
    print("=== Тест разбиения сообщений анализа ===")
    
    # Создаем длинный анализ
    long_analysis = "Это очень подробный анализ. " * 150  # Примерно 3000 символов
    
    parts = split_analysis_message(
        analysis_text=long_analysis,
        materials_count=25,
        category="Технологии",
        date="2025-01-13"
    )
    
    print(f"Анализ разбит на {len(parts)} частей")
    
    # Проверяем первую часть (должна содержать заголовок)
    first_part = parts[0]
    assert "✅ Анализ новостей завершен!" in first_part
    assert "📂 Категория: Технологии" in first_part
    assert "📅 Дата: 2025-01-13" in first_part
    assert "📊 Проанализировано материалов: 25" in first_part
    
    # Проверяем остальные части
    for i, part in enumerate(parts[1:], 2):
        assert "📝 Продолжение анализа:" in part
        print(f"Часть {i}: {len(part)} символов")
    
    print("✅ Тест анализа пройден\n")

def test_split_digest_message():
    """Тест разбиения дайджеста"""
    print("=== Тест разбиения дайджеста ===")
    
    # Создаем длинный дайджест
    long_digest = "📌 Категория: Технологии\n📊 Материалов: 10\n📝 Анализ: Это очень подробный анализ технологий. " * 100
    
    parts = split_digest_message(
        digest_text=long_digest,
        date="2025-01-13",
        total_materials=50
    )
    
    print(f"Дайджест разбит на {len(parts)} частей")
    
    # Проверяем первую часть
    first_part = parts[0]
    assert "📰 Ежедневный дайджест новостей за 2025-01-13" in first_part
    assert "📊 Всего проанализировано материалов: 50" in first_part
    
    # Проверяем остальные части
    for i, part in enumerate(parts[1:], 2):
        assert f"📰 Продолжение дайджеста (часть {i}):" in part
        print(f"Часть {i}: {len(part)} символов")
    
    print("✅ Тест дайджеста пройден\n")

def test_format_message_part():
    """Тест форматирования частей сообщения"""
    print("=== Тест форматирования частей сообщения ===")
    
    # Тест с одной частью
    single_part = format_message_part("Текст сообщения", 1, 1)
    assert "--- Часть 1 из 1 ---" not in single_part
    
    # Тест с несколькими частями
    multi_part = format_message_part("Текст сообщения", 2, 3)
    assert "--- Часть 2 из 3 ---" in multi_part
    
    print("✅ Тест форматирования пройден\n")

def test_edge_cases():
    """Тест граничных случаев"""
    print("=== Тест граничных случаев ===")
    
    # Пустое сообщение
    empty_parts = split_message("")
    assert len(empty_parts) == 1
    assert empty_parts[0] == ""
    
    # Сообщение точно на границе лимита
    boundary_text = "A" * 4096
    boundary_parts = split_message(boundary_text)
    assert len(boundary_parts) == 1
    assert len(boundary_parts[0]) == 4096
    
    # Сообщение чуть больше лимита
    over_limit_text = "A" * 4097
    over_limit_parts = split_message(over_limit_text)
    print(f"Текст длиной {len(over_limit_text)} разбит на {len(over_limit_parts)} частей")
    assert len(over_limit_parts) >= 2, f"Ожидалось минимум 2 части, получено {len(over_limit_parts)}"
    
    # Проверяем, что каждая часть не превышает лимит
    for i, part in enumerate(over_limit_parts):
        assert len(part) <= 4096, f"Часть {i+1} превышает лимит: {len(part)} символов"
        print(f"Часть {i+1}: {len(part)} символов")
    
    print("✅ Граничные случаи пройдены\n")

if __name__ == "__main__":
    print("Запуск тестов разбиения сообщений...\n")
    
    try:
        test_split_message()
        test_split_analysis_message()
        test_split_digest_message()
        test_format_message_part()
        test_edge_cases()
        
        print("🎉 Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 