# utils/sources_helpers.py

from typing import List, Set

def get_categories_set(sources: List[dict]) -> Set[str]:
    return set(src.get('category', 'Без категории') for src in sources)

def get_category_filter(category_hash: str, categories: Set[str]) -> str:
    from bot.utils.misc import callback_to_category
    return callback_to_category(category_hash, list(categories))

def filter_sources_by_category(sources: List[dict], category: str) -> List[dict]:
    if category == "all":
        return sources
    return [src for src in sources if src.get('category') == category]

def format_sources_text(category: str, total: int, page: int = 0, total_pages: int | None = None) -> str:
    # Проверяем, что категория не None
    if category is None:
        category = "Неизвестная категория"
    
    if total == 0:
        return f"🗂 Активные источники (категория: {category}):\n\n❌ Источники не найдены"
    text = f"🗂 Активные источники (категория: {category}):\n\n📊 Всего источников: {total}"
    if total_pages:
        text += f"\n📄 Страница {page+1} из {total_pages}"
    else:
        text += f"\n📄 Страница 1"
    return text
