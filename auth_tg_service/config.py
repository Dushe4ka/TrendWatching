import os
from dotenv import load_dotenv

load_dotenv()
 
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "tg_auth_service")
# Используем правильный URL для Redis Docker контейнера
REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/1")
SESSION_DIR = os.getenv("SESSION_DIR", "sessions/")
MAX_CHANNELS_PER_ACCOUNT = int(os.getenv("MAX_CHANNELS_PER_ACCOUNT", 100)) 
BLACKBOX_MONGO_URI = os.getenv("BLACKBOX_MONGO_URI", "mongodb://localhost:27017/")
BLACKBOX_DB = os.getenv("BLACKBOX_DB", "blackbox") 
API_ID = int(os.getenv("API_ID", "123456"))
API_HASH = os.getenv("API_HASH", "your_api_hash")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")