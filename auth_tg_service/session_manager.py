import os
from config import SESSION_DIR

if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

def get_session_file_path(phone_number: str) -> str:
    # Возвращаем путь без расширения .session, Telethon сам добавит его
    return os.path.join(SESSION_DIR, f"{phone_number}")

def session_exists(phone_number: str) -> bool:
    return os.path.exists(get_session_file_path(phone_number) + ".session")

def remove_session(phone_number: str):
    path = get_session_file_path(phone_number) + ".session"
    if os.path.exists(path):
        os.remove(path) 