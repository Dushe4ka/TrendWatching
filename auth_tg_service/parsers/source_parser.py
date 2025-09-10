import asyncio
import logging
from typing import List, Dict, Any
from .rss_parser import parse_rss
from .tg_parser import parse_tg_channel_distributed
from storage import get_sessions
from blackbox_storage import get_new_channels
import os
from .tg_parser import parse_tg_channel_with_session

log = logging.getLogger(__name__)

class SourceParser:
    """Основной класс для парсинга источников"""
    
    def __init__(self, parsed_data_collection, blackbox_db):
        """
        Инициализация парсера
        
        Args:
            parsed_data_collection: MongoDB коллекция для сохранения спарсенных данных
            blackbox_db: MongoDB база данных blackbox
        """
        self.parsed_data_collection = parsed_data_collection
        self.blackbox_db = blackbox_db
        self.sources_collection = blackbox_db["sources"]
    
    async def get_available_sources(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Получает доступные источники из blackbox
        
        Args:
            limit: Лимит источников для получения
            
        Returns:
            List[Dict]: Список источников
        """
        try:
            # Используем get_all_channels для парсинга всех источников
            from blackbox_storage import get_all_channels
            sources = await get_all_channels(limit=limit)
            log.info(f"Получено {len(sources)} источников для парсинга")
            return sources
        except Exception as e:
            log.error(f"Ошибка при получении источников: {e}")
            return []
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Получает активные сессии для парсинга
        
        Returns:
            List[Dict]: Список активных сессий
        """
        try:
            sessions = await get_sessions()
            active_sessions = [s for s in sessions if s.get('status') == 'active']
            log.info(f"Найдено {len(active_sessions)} активных сессий")
            return active_sessions
        except Exception as e:
            log.error(f"Ошибка при получении сессий: {e}")
            return []
    
    def categorize_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Категоризирует источники по типу
        
        Args:
            sources: Список источников
            
        Returns:
            Dict: Словарь с источниками по типам
        """
        categorized = {
            'rss': [],
            'telegram': []
        }
        
        for source in sources:
            source_type = source.get('type', '').lower()
            url = source.get('url', '').lower()
            
            # Улучшенная логика определения типа источника
            is_telegram = (
                'telegram' in source_type or 
                't.me' in url or 
                url.startswith('@') or
                url.startswith('https://t.me/') or
                url.startswith('http://t.me/') or
                url.startswith('https://telegram.me/') or
                url.startswith('http://telegram.me/')
            )
            
            if is_telegram:
                categorized['telegram'].append(source)
                log.info(f"Telegram источник: {url}")
            else:
                categorized['rss'].append(source)
                log.info(f"RSS источник: {url}")
        
        log.info(f"Категоризировано: {len(categorized['rss'])} RSS, {len(categorized['telegram'])} Telegram")
        return categorized
    
    async def parse_rss_sources(self, rss_sources: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Парсит RSS источники параллельно
        
        Args:
            rss_sources: Список RSS источников
            
        Returns:
            Dict: Результаты парсинга по источникам
        """
        log.info(f"Начинаем парсинг {len(rss_sources)} RSS источников")
        
        results = {}
        tasks = []
        
        for source in rss_sources:
            url = source.get('url')
            category = source.get('category', 'general')
            
            if not url:
                continue
                
            task = parse_rss(
                url=url,
                category=category,
                parsed_data_collection=self.parsed_data_collection,
                verbose=False
            )
            tasks.append((url, task))
        
        # Выполняем задачи параллельно
        if tasks:
            urls, coroutines = zip(*tasks)
            results_list = await asyncio.gather(*coroutines, return_exceptions=True)
            
            for url, result in zip(urls, results_list):
                if isinstance(result, Exception):
                    log.error(f"❌ Ошибка при парсинге RSS {url}: {result}")
                    results[url] = None
                else:
                    results[url] = result
        
        total_saved = sum(r for r in results.values() if r is not None)
        log.info(f"✅ RSS парсинг завершен. Всего спаршено: {total_saved}")
        
        return results

    async def parse_telegram_sources(self, tg_sources: List[Dict[str, Any]],
                                     sessions: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """
        Парсит Telegram источники по каналам, указанным в сессиях.

        Args:
            tg_sources: Список Telegram источников (может быть пустым, только для совместимости)
            sessions: Список активных сессий

        Returns:
            Dict: Результаты парсинга по источникам и сессиям
        """
        log.info(f"Начинаем парсинг Telegram источников по каналам из сессий ({len(sessions)} сессий)")

        results = {}

        if not sessions:
            log.warning("Нет активных сессий для парсинга Telegram")
            return results

        for session in sessions:
            session_phone = session.get("phone_number", "Unknown")
            session_channels = session.get("channels", [])

            if not session_channels:
                log.warning(f"Сессия {session_phone} не имеет каналов для парсинга")
                continue

            log.info(f"🚀 Парсим для сессии {session_phone} с {len(session_channels)} каналами")

            cleaned_sources = clean_mongodb_data(session_channels)
            session_result = await self.parse_telegram_sources_with_session(cleaned_sources, session_phone)

            # Результат сохраняем по URL канала
            results.update(session_result)

            log.info(f"✅ Сессия {session_phone} завершена. Спаршено: {sum(session_result.values())}")

        total_saved = sum(results.values())
        log.info(f"✅ Telegram парсинг завершен. Всего спаршено: {total_saved}")

        return results

    async def parse_telegram_sources_with_session(self, sources: list, session_phone: str) -> dict:
        """
        Парсит Telegram источники используя конкретную сессию
        
        Args:
            sources: Список Telegram источников (может быть список строк или список словарей)
            session_phone: Номер телефона сессии
            
        Returns:
            dict: Результаты парсинга по источникам
        """
        log.info(f"🔍 Начинаем парсинг с сессией {session_phone}")
        log.info(f"📊 Источников для парсинга: {len(sources)}")
        
        if not sources:
            log.warning("Нет Telegram источников для парсинга")
            return {}
        
        # Получаем API credentials
        api_id = int(os.getenv("API_ID", "0"))
        api_hash = os.getenv("API_HASH", "")
        
        if not api_id or not api_hash:
            log.error("❌ Не настроены API_ID или API_HASH")
            return {}
        
        log.info(f"✅ API credentials получены: api_id={api_id}, api_hash={'*' * len(api_hash) if api_hash else 'None'}")
        
        results = {}
        
        for i, source in enumerate(sources):
            try:
                # Обрабатываем как строки, так и словари
                if isinstance(source, str):
                    # Если source - это строка (URL канала)
                    source_url = source
                    category = 'general'
                elif isinstance(source, dict):
                    # Если source - это словарь
                    source_url = source.get('url', '')
                    category = source.get('category', 'general')
                else:
                    log.warning(f"⚠️ Неизвестный тип источника: {type(source)}")
                    continue
                
                if not source_url:
                    log.warning(f"⚠️ Пустой URL источника: {source}")
                    continue
                
                log.info(f"📱 Парсим источник {i+1}/{len(sources)}: {source_url}")
                
                # Парсим канал с конкретной сессией
                result = await parse_tg_channel_with_session(
                    source_url, 
                    category, 
                    session_phone,  # Передаем session_phone как phone_number
                    api_id, 
                    api_hash, 
                    self.parsed_data_collection
                )
                
                if result is not None:
                    results[source_url] = result
                    log.info(f"✅ Успешно спаршено {result} записей из {source_url}")
                else:
                    results[source_url] = 0
                    log.warning(f"⚠️ Не удалось спарсить {source_url}")
                    
            except Exception as e:
                # Безопасное получение URL для логирования
                source_url_for_log = source if isinstance(source, str) else source.get('url', '') if isinstance(source, dict) else str(source)
                log.error(f"❌ Ошибка при парсинге {source_url_for_log}: {e}")
                log.error(f"❌ Тип ошибки: {type(e).__name__}")
                results[source_url_for_log] = 0
        
        total_parsed = sum(results.values())
        log.info(f"🎉 Парсинг с сессией {session_phone} завершен. Всего спаршено: {total_parsed}")
        
        return results
    
    async def parse_all_sources(self, limit: int = 100) -> Dict[str, Any]:
        """
        Парсит все доступные источники параллельно
        
        Args:
            limit: Лимит источников для получения
            
        Returns:
            Dict: Общие результаты парсинга
        """
        log.info("🚀 Начинаем полный парсинг источников")
        
        # Получаем источники и сессии
        sources = await self.get_available_sources(limit)
        sessions = await self.get_active_sessions()
        
        if not sources:
            log.warning("Нет источников для парсинга")
            return {"error": "Нет источников для парсинга"}
        
        if not sessions:
            log.warning("Нет активных сессий")
            return {"error": "Нет активных сессий"}
        
        # Категоризируем источники
        categorized = self.categorize_sources(sources)
        
        # Парсим RSS и Telegram параллельно
        rss_task = self.parse_rss_sources(categorized['rss'])
        tg_task = self.parse_telegram_sources(categorized['telegram'], sessions)
        
        rss_results, tg_results = await asyncio.gather(rss_task, tg_task)
        
        # Подсчитываем общую статистику
        total_rss = sum(r for r in rss_results.values() if r is not None)
        total_tg = sum(
            sum(r.values()) if r and isinstance(r, dict) else 0 
            for r in tg_results.values() if r is not None
        )
        
        result = {
            "total_sources": len(sources),
            "rss_sources": len(categorized['rss']),
            "telegram_sources": len(categorized['telegram']),
            "active_sessions": len(sessions),
            "rss_parsed": total_rss,
            "telegram_parsed": total_tg,
            "total_parsed": total_rss + total_tg,
            "rss_results": rss_results,
            "telegram_results": tg_results
        }
        
        log.info(f"🎉 Парсинг завершен! Всего спаршено: {result['total_parsed']}")
        return result 