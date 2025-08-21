import os
import logging
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logger = logging.getLogger(__name__)

# Конфигурация для уведомлений
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

def send_admin_notification(text: str, chat_id=None):
    """Отправляет сообщение админу через Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN не установлен. Уведомление не отправлено.")
        return
    
    # Если указан конкретный chat_id, отправляем только туда
    if chat_id:
        chat_ids = [str(chat_id)]
    else:
        # Иначе отправляем во все админские чаты
        admin_chat_ids_str = os.getenv("ADMIN_CHAT_ID", "")
        if not admin_chat_ids_str:
            logger.warning("ADMIN_CHAT_ID не установлен. Уведомление не отправлено.")
            return
        chat_ids = [admin_chat_id.strip() for admin_chat_id in admin_chat_ids_str.split(",")]
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Отправляем сообщение в указанные чаты
    for chat_id in chat_ids:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Уведомление успешно отправлено админу (ID: {chat_id})")
        except requests.RequestException as e:
            logger.error(f"Не удалось отправить уведомление админу {chat_id}: {e}") 