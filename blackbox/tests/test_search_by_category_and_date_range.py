from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from vector_store import VectorStore
from logger_config import setup_logger

def test_search_by_category_and_date_range():
    logger = setup_logger("test_search_by_category_and_date_range")
    vector_store = VectorStore()

    # Получаем список категорий
    categories = vector_store.get_categories()
    if not categories:
        logger.error("Нет доступных категорий для теста!")
        return
    category = categories[0]
    logger.info(f"Тестируем категорию: {category}")

    # Определяем диапазон дат (например, неделя)
    # Берём сегодняшнюю дату как стартовую
    start_date = datetime.now() - timedelta(days=7)
    end_date = datetime.now()
    logger.info(f"Диапазон дат: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")

    # Выполняем поиск
    results = vector_store.search_by_category_and_date_range(
        category=category,
        start_date=start_date,
        end_date=end_date
    )

    logger.info(f"Найдено материалов: {len(results)}")
    if not results:
        logger.warning("Нет материалов в заданном диапазоне!")
        return

    # Проверяем, что все даты в диапазоне
    all_in_range = True
    for i, item in enumerate(results, 1):
        date_str = item.get('date', '')
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except Exception as e:
            logger.error(f"Ошибка парсинга даты у материала {i}: {date_str} ({e})")
            all_in_range = False
            continue
        if not (start_date.date() <= date_obj.date() <= end_date.date()):
            logger.error(f"Материал {i} вне диапазона: {date_str}")
            all_in_range = False
        logger.info(f"{i}. {item.get('title', '')} | {date_str} | {item.get('url', '')}")

    if all_in_range:
        logger.info("Все найденные материалы попадают в указанный диапазон дат.")
    else:
        logger.error("Обнаружены материалы вне диапазона дат!")

if __name__ == "__main__":
    test_search_by_category_and_date_range() 