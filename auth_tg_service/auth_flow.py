from telethon import TelegramClient
from config import SESSION_DIR
from session_manager import get_session_file_path
import os

API_ID = int(os.getenv("TG_API_ID", "123456"))  # заменить на свой
API_HASH = os.getenv("TG_API_HASH", "your_api_hash")  # заменить на свой

async def request_code(phone_number: str):
    session_file = get_session_file_path(phone_number)
    client = TelegramClient(session_file, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
    await client.disconnect()

async def confirm_code(phone_number: str, code: str):
    session_file = get_session_file_path(phone_number)
    client = TelegramClient(session_file, API_ID, API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        await client.sign_in(phone_number, code)
    await client.disconnect() 