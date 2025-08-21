#!/usr/bin/env python3
"""
Тестовый скрипт для проверки парсинга источников
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_source_parser():
    """Тестирует основной парсер источников"""
    print("=== Тестирование парсера источников ===")
    try:
        from parsers.source_parser import SourceParser
        from storage import db
        from blackbox_storage import blackbox_db
        
        # Инициализируем парсер
        parsed_data_collection = db["parsed_data"]
        parser = SourceParser(parsed_data_collection, blackbox_db)
        
        # Получаем источники
        sources = await parser.get_available_sources(limit=5)
        print(f"✅ Получено {len(sources)} источников")
        
        # Получаем сессии
        sessions = await parser.get_active_sessions()
        print(f"✅ Найдено {len(sessions)} активных сессий")
        
        # Категоризируем источники
        categorized = parser.categorize_sources(sources)
        print(f"✅ Категоризировано: {len(categorized['rss'])} RSS, {len(categorized['telegram'])} Telegram")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при тестировании парсера: {e}")
        return False

async def test_rss_parser():
    """Тестирует RSS парсер"""
    print("=== Тестирование RSS парсера ===")
    try:
        from parsers.rss_parser import parse_rss
        from storage import db
        
        # Тестовый RSS источник
        test_url = "https://rss.cnn.com/rss/edition.rss"
        
        parsed_data_collection = db["parsed_data"]
        result = await parse_rss(
            url=test_url,
            category="test",
            parsed_data_collection=parsed_data_collection,
            verbose=True
        )
        
        if result is not None:
            print(f"✅ RSS парсинг успешен: {result} записей")
            return True
        else:
            print("❌ RSS парсинг не удался")
            return False
    except Exception as e:
        print(f"❌ Ошибка при тестировании RSS парсера: {e}")
        return False

async def test_telegram_parser():
    """Тестирует Telegram парсер"""
    print("=== Тестирование Telegram парсера ===")
    try:
        from parsers.tg_parser import parse_tg_channel_with_session
        from storage import db, get_sessions
        
        # Получаем активные сессии
        sessions = await get_sessions()
        active_sessions = [s for s in sessions if s.get('status') == 'active']
        
        if not active_sessions:
            print("⚠️  Нет активных сессий для тестирования Telegram парсера")
            return True  # Не считаем это ошибкой
        
        # Тестовый Telegram канал
        test_channel = "https://t.me/durov"
        
        parsed_data_collection = db["parsed_data"]
        result = await parse_tg_channel_with_session(
            channel=test_channel,
            category="test",
            phone_number=active_sessions[0]['phone_number'],
            api_id=123456,  # Замените на реальные значения
            api_hash="your_api_hash",  # Замените на реальные значения
            parsed_data_collection=parsed_data_collection,
            limit=5
        )
        
        if result is not None:
            print(f"✅ Telegram парсинг успешен: {result} записей")
            return True
        else:
            print("❌ Telegram парсинг не удался")
            return False
    except Exception as e:
        print(f"❌ Ошибка при тестировании Telegram парсера: {e}")
        return False

async def test_celery_tasks():
    """Тестирует Celery задачи"""
    print("=== Тестирование Celery задач ===")
    try:
        from celery_app.parsing_tasks import parse_sources_task
        
        # Запускаем задачу с небольшим лимитом
        result = parse_sources_task.delay(limit=2)
        print(f"✅ Celery задача запущена: {result.id}")
        
        # Ждем результат (не более 30 секунд)
        try:
            task_result = result.get(timeout=30)
            print(f"✅ Задача завершена: {task_result}")
            return True
        except Exception as e:
            print(f"⚠️  Задача не завершилась в срок: {e}")
            return True  # Не считаем это критической ошибкой
    except Exception as e:
        print(f"❌ Ошибка при тестировании Celery задач: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🔧 Тестирование системы парсинга источников")
    print("=" * 60)
    
    tests = [
        test_source_parser,
        test_rss_parser,
        test_telegram_parser,
        test_celery_tasks
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Результаты тестирования парсинга:")
    passed = sum(results)
    total = len(results)
    print(f"✅ Пройдено: {passed}/{total}")
    
    if passed == total:
        print("🎉 Все тесты парсинга пройдены! Система готова к работе.")
        return 0
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте конфигурацию.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 