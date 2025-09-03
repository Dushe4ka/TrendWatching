import aiohttp
import asyncio
import feedparser
import logging
from .utils import retry_on_failure, decode_if_bytes, save_parsed_data

log = logging.getLogger(__name__)

async def fetch_rss_content(url, headers):
    """Получает содержимое RSS-ленты с таймаутами"""
    timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as response:
            return await response.text()

async def parse_rss(url: str, category: str, parsed_data_collection, verbose=False):
    """
    Парсит RSS ленту и сохраняет данные в MongoDB
    
    Args:
        url: URL RSS ленты
        category: Категория для спарсенных данных
        parsed_data_collection: MongoDB коллекция для сохранения данных
        verbose: Подробный вывод для отладки
    
    Returns:
        int: Количество спарсенных записей или None при ошибке
    """
    log.info(f"Начало парсинга RSS: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/rss+xml, text/xml;q=0.9, */*;q=0.8'
        }
        
        # Используем механизм повторных запросов с уменьшенными таймаутами
        content = await retry_on_failure(fetch_rss_content, url, headers, max_retries=2, delay=2)
        feed = feedparser.parse(content)
        
        if verbose:
            print("\n=== Отладочная информация ===")
            print(f"Фактический URL: {getattr(feed, 'href', url)}")
            print(f"Статус: {getattr(feed, 'status', 'N/A')}")
            if hasattr(feed, 'bozo_exception') and feed.bozo_exception:
                print(f"Ошибка парсера: {type(feed.bozo_exception).__name__}: {feed.bozo_exception}")
            print(f"Content-Type: {feed.headers.get('content-type', 'N/A')}")
            print(f"Версия: {getattr(feed, 'version', 'N/A')}")
            print(f"Кодировка: {getattr(feed, 'encoding', 'N/A')}")
            print(f"Заголовок канала: {feed.feed.get('title', 'N/A')}")
            print(f"Описание канала: {feed.feed.get('description', 'N/A')}")
            print(f"Всего записей: {len(feed.entries)}")
            if len(feed.entries) > 0:
                print("\nПример первой записи:")
                first_entry = feed.entries[0]
                print(f"Заголовок: {first_entry.get('title', 'N/A')}")
                print(f"Ссылка: {first_entry.get('link', 'N/A')}")
                print(f"Дата публикации: {first_entry.get('published', 'N/A')}")
                print(f"Доступные поля: {list(first_entry.keys())}")
            print("===========================\n")
            
        if feed.bozo and isinstance(feed.bozo_exception, feedparser.NonXMLContentType):
            log.error(f"Сервер вернул не XML (RSS) контент: {feed.headers.get('content-type', 'N/A')}")
            if verbose:
                print("Сырой ответ сервера:")
                print(f"Первые 200 символов:\n{content[:200]}")
            return None
            
        if not feed.entries:
            log.warning("RSS-лента не содержит записей")
            return None
        
        saved_count = 0
        for entry in feed.entries:
            data = {
                "url": decode_if_bytes(entry.link),
                "title": decode_if_bytes(entry.get('title', '')),
                "description": decode_if_bytes(entry.get('description', '')),
                "content": decode_if_bytes(entry.get('content', [{}])[0].get('value', '')) if hasattr(entry, 'content') else '',
                "date": entry.get('published', ''),
                "category": category,
                "source_type": "rss",
                "source_url": url
            }
            
            if await save_parsed_data(data, parsed_data_collection):
                saved_count += 1
                print(f"📄 RSS: {data['title'][:100]}... | {data['url']}")
            
        log.info(f"✅ Успешно спаршено {saved_count} записей из {url}")
        return saved_count
    except Exception as e:
        log.error(f"❌ Ошибка при парсинге RSS ({url}): {str(e)}")
        return None

async def test_rss_parser():
    """Функция для тестирования RSS парсера через консоль"""
    print("=== Тестирование RSS парсера ===")
    url = input("Введите URL RSS-ленты: ").strip()
    category = input("Введите категорию: ").strip()
    verbose = input("Показать отладочную информацию? (y/n): ").lower() == 'y'
    print("\nРезультаты парсинга:")
    result = await parse_rss(url, category, verbose)
    if result:
        print(f"\nУспешно спаршено {result} записей")
    else:
        print("\nПарсинг завершился с ошибкой или лента пуста")
        print("Проверьте:")
        print("- Доступность RSS-ленты (откройте в браузере)")
        print("- Корректность URL")
        print("- Наличие записей в ленте")

if __name__ == "__main__":
    asyncio.run(test_rss_parser())
