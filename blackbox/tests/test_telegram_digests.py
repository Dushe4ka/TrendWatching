#!/usr/bin/env python3
"""
Скрипт для тестирования системы планировщика дайджестов Telegram каналов
"""
import os
import sys
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
load_dotenv()

from celery_app import app
from celery_app.tasks.telegram_digest_tasks import send_test_digest, schedule_daily_digests
from telegram_channels_service import telegram_channels_service
from datetime import datetime, timedelta

def test_digest_system():
    """Тестирование системы дайджестов"""
    print("🧪 Тестирование системы планировщика дайджестов Telegram каналов")
    print("=" * 70)
    
    try:
        # 1. Проверяем подключение к Celery
        print("1️⃣ Проверка подключения к Celery...")
        i = app.control.inspect()
        active_tasks = i.active()
        if active_tasks:
            print("✅ Celery подключен, активные задачи найдены")
        else:
            print("⚠️ Celery подключен, но активных задач нет")
        
        # 2. Получаем список активных дайджестов
        print("\n2️⃣ Получение списка активных дайджестов...")
        active_digests = telegram_channels_service.get_active_digests()
        print(f"📊 Найдено активных дайджестов: {len(active_digests)}")
        
        if active_digests:
            for i, digest in enumerate(active_digests, 1):
                print(f"   {i}. Канал: {digest['channel_id']}, Категория: {digest['category']}, Время: {digest['time']}")
        else:
            print("   ❌ Активных дайджестов не найдено")
            print("   💡 Создайте дайджест через админскую панель бота")
            return
        
        # 3. Тестируем отправку дайджеста (отложенная задача)
        print("\n3️⃣ Тестирование отправки дайджеста...")
        if active_digests:
            test_digest = active_digests[0]
            print(f"   📤 Отправляем тестовый дайджест для канала {test_digest['channel_id']}")
            
            # Отправляем тестовый дайджест через 1 минуту
            future_time = datetime.now() + timedelta(minutes=1)
            result = send_test_digest.apply_async(
                args=[test_digest['channel_id'], test_digest['category']],
                eta=future_time
            )
            
            print(f"   ✅ Задача запланирована с ID: {result.id}")
            print(f"   ⏰ Время выполнения: {future_time.strftime('%H:%M:%S')}")
            print(f"   📋 Статус: {result.status}")
        
        # 4. Тестируем планировщик дайджестов
        print("\n4️⃣ Тестирование планировщика дайджестов...")
        print("   📅 Планируем дайджесты на завтра...")
        
        # Запускаем планировщик вручную
        result = schedule_daily_digests.delay()
        print(f"   ✅ Задача планирования запущена с ID: {result.id}")
        
        # Ждем результат
        print("   ⏳ Ожидаем результат планирования...")
        try:
            schedule_result = result.get(timeout=30)
            print(f"   📊 Результат планирования: {schedule_result}")
        except Exception as e:
            print(f"   ❌ Ошибка получения результата: {str(e)}")
        
        # 5. Показываем информацию о системе
        print("\n5️⃣ Информация о системе:")
        print("   🔧 Celery Beat: планирует задачи каждый день в 00:01")
        print("   📱 Telegram Bot: отправляет дайджесты в указанное время")
        print("   🧠 AI Analysis: использует существующую функцию analyze_trend")
        print("   💾 MongoDB: хранит настройки дайджестов")
        print("   🚀 Redis: брокер сообщений для Celery")
        
        print("\n✅ Тестирование завершено успешно!")
        print("\n💡 Для мониторинга задач используйте:")
        print("   - Celery Flower: http://localhost:5555")
        print("   - Celery CLI: celery -A celery_app inspect active")
        print("   - Логи: tail -f logs/celery.log")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()

def show_digest_status():
    """Показать статус дайджестов"""
    print("\n📊 Статус дайджестов:")
    print("=" * 50)
    
    try:
        active_digests = telegram_channels_service.get_active_digests()
        
        if not active_digests:
            print("❌ Активных дайджестов не найдено")
            return
        
        print(f"📈 Всего активных дайджестов: {len(active_digests)}")
        print()
        
        for i, digest in enumerate(active_digests, 1):
            print(f"🔹 Дайджест {i}:")
            print(f"   📱 Канал ID: {digest['channel_id']}")
            print(f"   🏷️ Категория: {digest['category']}")
            print(f"   ⏰ Время отправки: {digest['time']}")
            print(f"   🆔 Digest ID: {digest['digest_id']}")
            print()
        
        # Показываем время следующего планирования
        tomorrow = datetime.now().date() + timedelta(days=1)
        print(f"📅 Следующее планирование: {tomorrow.strftime('%d.%m.%Y')} в 00:01")
        
    except Exception as e:
        print(f"❌ Ошибка получения статуса: {str(e)}")

if __name__ == "__main__":
    print("🚀 Запуск тестирования системы дайджестов Telegram каналов")
    print("=" * 70)
    
    # Показываем статус дайджестов
    show_digest_status()
    
    # Запрашиваем подтверждение на тестирование
    response = input("\n🧪 Запустить тестирование системы? (y/N): ").strip().lower()
    
    if response in ['y', 'yes', 'да']:
        test_digest_system()
    else:
        print("❌ Тестирование отменено")
        print("\n💡 Для ручного тестирования используйте:")
        print("   - send_test_digest.delay(channel_id, category)")
        print("   - schedule_daily_digests.delay()")
        print("   - send_channel_digest.delay(channel_id, digest_id, category, time)") 