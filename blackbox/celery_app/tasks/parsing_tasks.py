import os
import requests
from celery import shared_task
from datetime import datetime, timedelta
from logger_config import setup_logger

# Настраиваем логгер
logger = setup_logger("parsing_tasks")

# URL сервиса авторизации для парсинга
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")

@shared_task
def periodic_parse_all_sources():
    """Периодическая задача для парсинга всех источников"""
    try:
        logger.info("🚀 Запуск периодического парсинга всех источников")
        
        # Вызываем API сервиса авторизации для парсинга
        response = requests.post(
            f"{AUTH_SERVICE_URL}/parsing/parse_all_sources",
            json={"limit": 100, "chat_id": None},
            timeout=300  # 5 минут на выполнение
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Периодический парсинг завершен успешно: {result}")
            
            # Запускаем векторизацию после парсинга
            try:
                vectorization_response = requests.post(
                    f"{AUTH_SERVICE_URL}/vectorization/start",
                    json={},
                    timeout=60
                )
                if vectorization_response.status_code == 200:
                    logger.info("✅ Векторизация запущена после парсинга")
                else:
                    logger.warning(f"⚠️ Не удалось запустить векторизацию: {vectorization_response.status_code}")
            except Exception as e:
                logger.error(f"❌ Ошибка при запуске векторизации: {e}")
            
            return result
        else:
            logger.error(f"❌ Ошибка при периодическом парсинге: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка в периодической задаче парсинга: {e}")
        return None

@shared_task
def periodic_parse_rss_sources():
    """Периодическая задача для парсинга RSS источников"""
    try:
        logger.info("🚀 Запуск периодического парсинга RSS источников")
        
        response = requests.post(
            f"{AUTH_SERVICE_URL}/parsing/parse_rss_sources",
            json={"limit": 50, "chat_id": None},
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Периодический RSS парсинг завершен: {result}")
            return result
        else:
            logger.error(f"❌ Ошибка при RSS парсинге: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка в периодической задаче RSS парсинга: {e}")
        return None

@shared_task
def periodic_parse_telegram_sources():
    """Периодическая задача для парсинга Telegram источников"""
    try:
        logger.info("🚀 Запуск периодического парсинга Telegram источников")
        
        response = requests.post(
            f"{AUTH_SERVICE_URL}/parsing/parse_telegram_sources",
            json={"limit": 50, "chat_id": None},
            timeout=300
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Периодический Telegram парсинг завершен: {result}")
            
            # Запускаем векторизацию после парсинга
            try:
                vectorization_response = requests.post(
                    f"{AUTH_SERVICE_URL}/vectorization/start",
                    json={},
                    timeout=60
                )
                if vectorization_response.status_code == 200:
                    logger.info("✅ Векторизация запущена после Telegram парсинга")
                else:
                    logger.warning(f"⚠️ Не удалось запустить векторизацию: {vectorization_response.status_code}")
            except Exception as e:
                logger.error(f"❌ Ошибка при запуске векторизации: {e}")
            
            return result
        else:
            logger.error(f"❌ Ошибка при Telegram парсинге: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка в периодической задаче Telegram парсинга: {e}")
        return None

@shared_task
def cleanup_old_data():
    """Периодическая задача для очистки старых данных"""
    try:
        logger.info("🧹 Запуск очистки старых данных")
        
        # Здесь можно добавить логику очистки старых записей
        # Например, удаление записей старше 30 дней
        
        logger.info("✅ Очистка старых данных завершена")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке старых данных: {e}")
        return False 