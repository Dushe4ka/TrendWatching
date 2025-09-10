import logging
from celery_app.celery_config import celery_app
from parsers.source_parser import SourceParser
from storage import db
from blackbox_storage import blackbox_db
from celery_app.utils import monitor_performance, run_async
import os
import asyncio
import httpx
import requests

log = logging.getLogger(__name__)

# Конфигурация для микросервиса векторизации
VECTORIZATION_SERVICE_URL = os.getenv("VECTORIZATION_SERVICE_URL", "http://localhost:8001")

async def call_vectorization_service(chat_id: str = None):
    """Вызывает микросервис векторизации после завершения парсинга"""
    try:
        # Ждем немного, чтобы парсинг точно завершился
        import time
        time.sleep(5)
        
        payload = {}
        if chat_id:
            payload["chat_id"] = str(chat_id)
        
        response = requests.post(
            f"{VECTORIZATION_SERVICE_URL}/vectorization/start",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            log.info(f"✅ Векторизация запущена: {result}")
            return result
        else:
            log.error(f"❌ Ошибка при вызове микросервиса векторизации: {response.status_code}")
            return None
    except Exception as e:
        log.error(f"❌ Ошибка при вызове микросервиса векторизации: {e}")
        return None

async def send_parsing_stats_to_telegram(stats: dict, chat_id: str = None):
    """Отправляет статистику парсинга в Telegram чат и запускает векторизацию"""
    try:
        from aiogram import Bot
        from config import TELEGRAM_BOT_TOKEN
        
        if not chat_id:
            chat_id = os.getenv("ADMIN_CHAT_ID")
        
        if not chat_id or not TELEGRAM_BOT_TOKEN:
            log.warning("Не удалось отправить статистику: отсутствует chat_id или TELEGRAM_BOT_TOKEN")
            return
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        # Формируем сообщение со статистикой
        message = f"""📊 Статистика парсинга

Источники:
• Всего источников: {stats.get('total_sources', 0)}
• RSS источников: {stats.get('rss_sources', 0)}
• Telegram источников: {stats.get('telegram_sources', 0)}
• Активных сессий: {stats.get('active_sessions', 0)}

Спарсенные записи:
• Всего записей: {stats.get('total_parsed', 0)}
• RSS записей: {stats.get('rss_parsed', 0)}
• Telegram записей: {stats.get('telegram_parsed', 0)}

Время выполнения: {stats.get('execution_time', 'N/A')}"""
        
        await bot.send_message(chat_id=chat_id, text=message)
        await bot.session.close()
        log.info(f"Статистика отправлена в чат {chat_id}")
        
        # Запускаем векторизацию после парсинга только если есть новые данные
        total_parsed = stats.get('total_parsed', 0)
        if total_parsed > 0:
            log.info(f"🔄 Запускаем векторизацию после парсинга ({total_parsed} новых записей)...")
            vectorization_result = await call_vectorization_service(chat_id)
            if vectorization_result:
                log.info("✅ Векторизация успешно запущена")
            else:
                log.warning("⚠️ Не удалось запустить векторизацию")
        else:
            log.info("ℹ️ Нет новых данных для векторизации")
        
    except Exception as e:
        log.error(f"Ошибка при отправке статистики в Telegram: {e}")

async def send_session_parsing_stats_to_telegram(stats: dict, chat_id: str):
    """Отправляет статистику парсинга по сессии в Telegram"""
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token or not chat_id:
            return
        
        session_phone = stats.get('session_phone', 'Unknown')
        sources_count = stats.get('sources_count', 0)
        parsed_count = stats.get('parsed_count', 0)
        execution_time = stats.get('execution_time', '0s')
        
        message = f"""
🔍 **Статистика парсинга по сессии**

📱 **Сессия:** `{session_phone}`
📊 **Источников:** {sources_count}
✅ **Спаршено:** {parsed_count}
⏱️ **Время:** {execution_time}

🎉 Парсинг завершен!
        """.strip()
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=10)
            if response.status_code == 200:
                log.info(f"✅ Статистика отправлена в Telegram (chat_id: {chat_id})")
            else:
                log.error(f"❌ Ошибка отправки в Telegram: {response.text}")
                
    except Exception as e:
        log.error(f"Ошибка при отправке статистики в Telegram: {e}")

def clean_mongodb_data(data):
    """Очищает данные от MongoDB ObjectId для JSON сериализации"""
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
                cleaned[key] = str(value)
            elif isinstance(value, (dict, list)):
                cleaned[key] = clean_mongodb_data(value)
            else:
                cleaned[key] = value
        return cleaned
    elif isinstance(data, list):
        return [clean_mongodb_data(item) for item in data]
    else:
        return data

@celery_app.task
@monitor_performance
def parse_telegram_with_session_task(session_phone: str, sources: list, chat_id: str = None):
    """Парсит Telegram источники с конкретной сессией"""
    import time
    start_time = time.time()
    
    async def inner():
        try:
            parsed_data_collection = db["parsed_data"]
            parser = SourceParser(parsed_data_collection, blackbox_db)
            
            # Очищаем источники от ObjectId
            cleaned_sources = clean_mongodb_data(sources)
            
            # Парсим только с указанной сессией
            result = await parser.parse_telegram_sources_with_session(cleaned_sources, session_phone)
            
            execution_time = time.time() - start_time
            
            # Безопасный подсчет результатов
            total_parsed = 0
            if result and isinstance(result, dict):
                for count in result.values():
                    if count is not None:
                        total_parsed += count
            
            stats = {
                "session_phone": session_phone,
                "sources_count": len(cleaned_sources),
                "parsed_count": total_parsed,
                "execution_time": f"{execution_time:.2f}s"
            }
            
            log.info(f"✅ Парсинг с сессией {session_phone} завершен. Спаршено: {total_parsed}")
            
            # Отправляем статистику в Telegram
            if chat_id:
                await send_parsing_stats_to_telegram(stats, chat_id)
            
            return {
                "session_phone": session_phone,
                "sources": cleaned_sources,
                "parsed": total_parsed,
                "results": result
            }
            
        except Exception as e:
            log.error(f"Ошибка при парсинге с сессией {session_phone}: {e}")
            return {"error": str(e)}
    
    return run_async(inner)

@celery_app.task
@monitor_performance
def parse_sources_task(limit: int = None, chat_id: str = None):
    """Парсит все источники (RSS + Telegram) с использованием каналов из сессий"""
    import time
    start_time = time.time()

    async def inner():
        try:
            parsed_data_collection = db["parsed_data"]
            parser = SourceParser(parsed_data_collection, blackbox_db)

            # Получаем источники и сессии
            sources = await parser.get_available_sources(limit)
            sessions = await parser.get_active_sessions()

            log.info(f"📊 Получено {len(sources)} источников и {len(sessions)} сессий")

            if not sources:
                log.warning("Нет источников для парсинга")
                return {"error": "Нет источников для парсинга"}

            # Категоризируем источники
            categorized = parser.categorize_sources(sources)
            log.info(f"📋 Категоризировано: {len(categorized['rss'])} RSS, {len(categorized['telegram'])} Telegram")

            # Парсим RSS источники
            log.info("📰 Начинаем парсинг RSS источников")
            rss_results = await parser.parse_rss_sources(categorized['rss'])
            total_rss = sum(r for r in rss_results.values() if r is not None)
            log.info(f"✅ RSS парсинг завершен. Спаршено: {total_rss}")

            # Парсим Telegram источники по каналам из сессий
            tg_results = []
            total_tg = 0
            for session in sessions:
                session_phone = session.get("phone_number", "Unknown")
                session_channels = session.get("channels", [])
                if session_channels:
                    log.info(f"🚀 Парсим для сессии {session_phone} с {len(session_channels)} каналами")
                    cleaned_session_sources = clean_mongodb_data(session_channels)
                    result = await parser.parse_telegram_sources_with_session(cleaned_session_sources, session_phone)
                    session_total = sum(result.values()) if result else 0
                    total_tg += session_total
                    tg_results.append({
                        "session_phone": session_phone,
                        "sources": cleaned_session_sources,
                        "parsed": session_total,
                        "results": result
                    })
                    log.info(f"✅ Сессия {session_phone} завершена. Спаршено: {session_total}")

            execution_time = time.time() - start_time

            result = {
                "total_sources": len(sources),
                "rss_sources": len(categorized['rss']),
                "telegram_sources": len(categorized['telegram']),
                "active_sessions": len(sessions),
                "rss_parsed": total_rss,
                "telegram_parsed": total_tg,
                "total_parsed": total_rss + total_tg,
                "rss_results": rss_results,
                "telegram_results": tg_results,
                "execution_time": f"{execution_time:.2f}s"
            }

            log.info(f"🎉 Парсинг завершен! Всего спаршено: {result['total_parsed']}")

            await send_parsing_stats_to_telegram(result, chat_id)
            return result

        except Exception as e:
            log.error(f"❌ Ошибка при парсинге источников: {e}")
            import traceback
            log.error(f"❌ Traceback: {traceback.format_exc()}")
            return {"error": str(e)}

    return run_async(inner)

@celery_app.task
@monitor_performance
def parse_rss_sources_task(limit: int = 50, chat_id: str = None):
    """Парсит только RSS источники"""
    import time
    start_time = time.time()
    
    async def inner():
        try:
            parsed_data_collection = db["parsed_data"]
            parser = SourceParser(parsed_data_collection, blackbox_db)
            
            sources = await parser.get_available_sources(limit)
            categorized = parser.categorize_sources(sources)
            
            result = await parser.parse_rss_sources(categorized['rss'])
            
            execution_time = time.time() - start_time
            total_parsed = sum(r for r in result.values() if r is not None)
            
            stats = {
                "total_sources": len(sources),
                "rss_sources": len(categorized['rss']),
                "telegram_sources": len(categorized['telegram']),
                "active_sessions": 0,
                "rss_parsed": total_parsed,
                "telegram_parsed": 0,
                "total_parsed": total_parsed,
                "execution_time": f"{execution_time:.2f}s"
            }
            
            log.info(f"✅ RSS парсинг завершен. Всего спаршено: {total_parsed}")
            
            # Отправляем статистику в Telegram
            await send_parsing_stats_to_telegram(stats, chat_id)
            
            return {
                "rss_sources": len(categorized['rss']),
                "rss_parsed": total_parsed,
                "rss_results": result
            }
            
        except Exception as e:
            log.error(f"Ошибка при парсинге RSS источников: {e}")
            return {"error": str(e)}
    
    return run_async(inner)

@celery_app.task
@monitor_performance
def parse_telegram_sources_task(limit: int = 50, chat_id: str = None):
    """Парсит только Telegram источники по каналам из сессий"""
    import time
    start_time = time.time()

    async def inner():
        try:
            parsed_data_collection = db["parsed_data"]
            parser = SourceParser(parsed_data_collection, blackbox_db)

            # Получаем источники и сессии
            sources = await parser.get_available_sources(limit)
            sessions = await parser.get_active_sessions()

            log.info(f"📊 Получено {len(sources)} источников и {len(sessions)} сессий")

            if not sources:
                log.warning("Нет источников для парсинга")
                return {"error": "Нет источников для парсинга"}

            categorized = parser.categorize_sources(sources)
            log.info(f"📋 Категоризировано: {len(categorized['rss'])} RSS, {len(categorized['telegram'])} Telegram")

            # Парсим Telegram источники только из channels сессий
            tg_results = []
            total_tg = 0
            for session in sessions:
                session_phone = session.get("phone_number", "Unknown")
                session_channels = session.get("channels", [])
                if session_channels:
                    log.info(f"🚀 Парсим для сессии {session_phone} с {len(session_channels)} каналами")
                    cleaned_session_sources = clean_mongodb_data(session_channels)
                    result = await parser.parse_telegram_sources_with_session(cleaned_session_sources, session_phone)
                    session_total = sum(result.values()) if result else 0
                    total_tg += session_total
                    tg_results.append({
                        "session_phone": session_phone,
                        "sources": cleaned_session_sources,
                        "parsed": session_total,
                        "results": result
                    })
                    log.info(f"✅ Сессия {session_phone} завершена. Спаршено: {session_total}")

            execution_time = time.time() - start_time

            stats = {
                "total_sources": len(sources),
                "rss_sources": len(categorized['rss']),
                "telegram_sources": len(categorized['telegram']),
                "active_sessions": len(sessions),
                "rss_parsed": 0,
                "telegram_parsed": total_tg,
                "total_parsed": total_tg,
                "execution_time": f"{execution_time:.2f}s"
            }

            log.info(f"✅ Telegram парсинг завершен. Всего спаршено: {total_tg}")

            await send_parsing_stats_to_telegram(stats, chat_id)
            return {
                "telegram_sources": len(categorized['telegram']),
                "telegram_parsed": total_tg,
                "telegram_results": tg_results
            }

        except Exception as e:
            log.error(f"❌ Ошибка при парсинге Telegram источников: {e}")
            import traceback
            log.error(f"❌ Traceback: {traceback.format_exc()}")
            return {"error": str(e)}

    return run_async(inner)

@celery_app.task
@monitor_performance
def parse_specific_source_task(source_url: str, source_type: str = "auto", chat_id: str = None):
    """Парсит конкретный источник"""
    import time
    start_time = time.time()
    
    async def inner():
        try:
            parsed_data_collection = db["parsed_data"]
            parser = SourceParser(parsed_data_collection, blackbox_db)
            
            # Парсим конкретный источник
            result = await parser.parse_specific_source(source_url, source_type)
            
            execution_time = time.time() - start_time
            
            stats = {
                "total_sources": 1,
                "rss_sources": 1 if source_type == "rss" else 0,
                "telegram_sources": 1 if source_type == "telegram" else 0,
                "active_sessions": 0,
                "rss_parsed": result if source_type == "rss" else 0,
                "telegram_parsed": result if source_type == "telegram" else 0,
                "total_parsed": result,
                "execution_time": f"{execution_time:.2f}s"
            }
            
            log.info(f"Парсинг источника {source_url} завершен: {result}")
            
            # Отправляем статистику в Telegram
            await send_parsing_stats_to_telegram(stats, chat_id)
            
            return {
                "source_url": source_url,
                "source_type": source_type,
                "parsed": result
            }
            
        except Exception as e:
            log.error(f"Ошибка при парсинге источника {source_url}: {e}")
            return {"error": str(e)}
    
    return run_async(inner) 