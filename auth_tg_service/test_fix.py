#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений в auth_tg_service
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import get_sessions
from blackbox_storage import get_new_channels

async def test_storage():
    """Тестирует работу с хранилищем"""
    print("=== Тестирование хранилища ===")
    try:
        sessions = await get_sessions()
        print(f"✅ Успешно получено {len(sessions)} сессий из MongoDB")
        return True
    except Exception as e:
        print(f"❌ Ошибка при получении сессий: {e}")
        return False

async def test_blackbox_storage():
    """Тестирует работу с blackbox хранилищем"""
    print("=== Тестирование blackbox хранилища ===")
    try:
        channels = await get_new_channels(limit=5)
        print(f"✅ Успешно получено {len(channels)} каналов из blackbox")
        return True
    except Exception as e:
        print(f"❌ Ошибка при получении каналов: {e}")
        return False

async def test_async_function():
    """Тестирует работу async функций"""
    print("=== Тестирование async функций ===")
    try:
        from celery_app.tasks import run_async
        
        async def test_coro():
            return "Тест успешен"
        
        result = run_async(test_coro)
        print(f"✅ Async функция работает: {result}")
        return True
    except Exception as e:
        print(f"❌ Ошибка в async функции: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🔧 Тестирование исправлений в auth_tg_service")
    print("=" * 50)
    
    tests = [
        test_storage,
        test_blackbox_storage,
        test_async_function
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {test.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Результаты тестирования:")
    passed = sum(results)
    total = len(results)
    print(f"✅ Пройдено: {passed}/{total}")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Исправления работают корректно.")
        return 0
    else:
        print("⚠️  Некоторые тесты не пройдены. Проверьте конфигурацию.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 