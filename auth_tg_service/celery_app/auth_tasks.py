import os
import json
import logging
import redis
import asyncio
import time
from celery import shared_task
from celery_app.celery_config import celery_app
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, AuthRestartError
from session_manager import get_session_file_path, session_exists, remove_session
from storage import db, get_session_by_phone, update_session_by_phone, create_channel_binding, get_channel_bindings, create_session
from blackbox_storage import blackbox_db, get_new_channels, mark_channel_assigned
from config import SESSION_DIR, MAX_CHANNELS_PER_ACCOUNT, API_ID, API_HASH, TELEGRAM_BOT_TOKEN, ADMIN_CHAT_ID
from datetime import datetime
from uuid import uuid4
from asgiref.sync import async_to_sync
from celery_app.utils import monitor_performance, run_async

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Redis клиент
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

AUTH_STATE_KEY_PREFIX = "telegram_auth_state:"

def send_admin_notification(text: str, chat_id=None):
    if not TELEGRAM_BOT_TOKEN or not ADMIN_CHAT_ID:
        return
    import requests
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id or ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        log.warning(f"Не удалось отправить уведомление админу: {e}")

def cleanup_expired_auth_states():
    """Очищает устаревшие состояния авторизации из Redis"""
    try:
        pattern = f"{AUTH_STATE_KEY_PREFIX}*"
        keys = redis_client.keys(pattern)
        cleaned_count = 0
        
        for key in keys:
            # Проверяем TTL ключа
            ttl = redis_client.ttl(key)
            if ttl == -1:  # Ключ без TTL
                redis_client.delete(key)
                cleaned_count += 1
                log.info(f"🗑️ Удален ключ без TTL: {key}")
            elif ttl == -2:  # Ключ не существует
                cleaned_count += 1
                log.info(f"🗑️ Ключ не существует: {key}")
        
        if cleaned_count > 0:
            log.info(f"🧹 Очищено {cleaned_count} устаревших состояний авторизации")
        
    except Exception as e:
        log.error(f"❌ Ошибка при очистке состояний авторизации: {e}")

# --- Celery задачи ---

@celery_app.task
@monitor_performance
def request_code_task(phone_number: str, api_id: int, api_hash: str, admin_chat_id: str = None):
    """Запрашивает код для авторизации Telegram аккаунта."""
    async def inner():
        # Очищаем устаревшие состояния перед запросом нового кода
        cleanup_expired_auth_states()
        
        session_file = get_session_file_path(phone_number)
        client = TelegramClient(session_file, api_id, api_hash)
        auth_key = f"{AUTH_STATE_KEY_PREFIX}{phone_number}"
        
        log.info(f"📱 Запрашиваем код для {phone_number}")
        
        try:
            await client.connect()
            if await client.is_user_authorized():
                log.info(f"✅ Аккаунт {phone_number} уже авторизован.")
                return {"status": "already_authorized", "phone_number": phone_number}
            
            log.info(f"📤 Отправляем запрос кода на {phone_number}")
            sent_code = await client.send_code_request(phone_number)
            
            state = {
                "status": "awaiting_code",
                "phone_code_hash": sent_code.phone_code_hash,
                "requested_at": datetime.utcnow().isoformat()
            }
            redis_client.set(auth_key, json.dumps(state), ex=1800)  # 30 минут вместо 600
            
            log.info(f"✅ Код отправлен на {phone_number}. TTL: 30 минут")
            return {"status": "code_sent", "phone_number": phone_number}
            
        except Exception as e:
            log.error(f"❌ Ошибка при отправке кода: {e}")
            log.error(f"❌ Тип ошибки: {type(e).__name__}")
            return {"status": "error", "error": str(e)}
        finally:
            try:
                if client.is_connected():
                    await client.disconnect()
                    log.info(f"🔌 Отключение от Telegram для {phone_number}")
            except Exception as disconnect_error:
                log.warning(f"⚠️ Ошибка при disconnect: {disconnect_error}")
    return run_async(inner)

@celery_app.task
@monitor_performance
def confirm_code_task(phone_number: str, code: str, api_id: int, api_hash: str, admin_chat_id: str = None):
    """Подтверждает код для авторизации Telegram аккаунта."""
    async def inner():
        session_file = get_session_file_path(phone_number)
        client = TelegramClient(session_file, api_id, api_hash)
        auth_key = f"{AUTH_STATE_KEY_PREFIX}{phone_number}"
        
        log.info(f"🔍 Начинаем подтверждение кода для {phone_number}")
        log.info(f"🔍 Ключ Redis: {auth_key}")
        
        state_raw = redis_client.get(auth_key)
        if not state_raw:
            msg = f"Процесс авторизации для {phone_number} не запущен. Сначала запросите код."
            log.warning(f"❌ {msg}")
            log.warning(f"❌ Состояние в Redis не найдено для ключа: {auth_key}")
            send_admin_notification(f"❌ {msg}", chat_id=admin_chat_id)
            return {"status": "error", "error": msg}
        
        log.info(f"✅ Состояние найдено в Redis для {phone_number}")
        auth_state = json.loads(state_raw)
        current_status = auth_state.get("status")
        log.info(f"📋 Текущий статус: {current_status}")
        
        try:
            await client.connect()
            log.info(f"🔗 Подключение к Telegram установлено для {phone_number}")
            
            if current_status == "awaiting_code":
                log.info(f"📱 Подтверждаем код для {phone_number}")
                try:
                    await client.sign_in(
                        phone=phone_number,
                        code=code,
                        phone_code_hash=auth_state["phone_code_hash"]
                    )
                    log.info(f"✅ Код успешно подтвержден для {phone_number}")
                except Exception as sign_in_error:
                    log.error(f"❌ Ошибка при sign_in: {sign_in_error}")
                    log.error(f"❌ Тип ошибки sign_in: {type(sign_in_error).__name__}")
                    raise sign_in_error
            elif current_status == "awaiting_password":
                log.info(f"🔐 Подтверждаем пароль 2FA для {phone_number}")
                await client.sign_in(password=code)
                log.info(f"✅ Пароль 2FA успешно подтвержден для {phone_number}")
            
            # Сохраняем сессию
            if hasattr(client.session, 'save'):
                if asyncio.iscoroutinefunction(client.session.save):
                    await client.session.save()
                else:
                    client.session.save()
            
            session_file_path = f"{session_file}.session"
            if os.path.exists(session_file_path):
                session_size = os.path.getsize(session_file_path)
                log.info(f"💾 Сессия сохранена: {session_file_path}, {session_size} байт")
                
                # --- Сохраняем сессию в MongoDB ---
                # Проверяем, есть ли уже сессия для этого номера
                existing = await get_session_by_phone(phone_number)
                if not existing:
                    session_id = str(uuid4())
                    session_data = {
                        "session_id": session_id,
                        "phone_number": phone_number,
                        "session_file_path": session_file_path,
                        "created_at": datetime.utcnow().isoformat(),
                        "channels": [],
                        "status": "active"  # Добавляем статус
                    }
                    await create_session(session_data)
                    log.info(f"📊 Сессия {phone_number} сохранена в MongoDB")
                # ---
            else:
                log.warning(f"⚠️ Сессия не сохранилась для {phone_number}")
                send_admin_notification(f"⚠️ Авторизация прошла, но сессия не сохранилась для {phone_number}", chat_id=admin_chat_id)
            
            redis_client.delete(auth_key)
            log.info(f"🗑️ Состояние авторизации удалено из Redis для {phone_number}")
            
            # Перераспределение каналов будет выполнено в боте после получения статуса
            log.info(f"✅ Авторизация {phone_number} завершена успешно")
            
            return {"status": "confirmed", "phone_number": phone_number}
            
        except SessionPasswordNeededError as e:
            log.info(f"🔐 Обнаружена 2FA для {phone_number}: {e}")
            auth_state["status"] = "awaiting_password"
            redis_client.set(auth_key, json.dumps(auth_state), ex=1800)  # 30 минут вместо 600
            return {"status": "awaiting_password", "phone_number": phone_number}
        except PhoneCodeInvalidError:
            log.warning(f"❌ Неверный код для {phone_number}")
            return {"status": "invalid_code", "phone_number": phone_number}
        except AuthRestartError:
            log.info(f"🔄 Перезапуск авторизации для {phone_number} из-за AuthRestartError")
            # Удаляем текущее состояние авторизации, чтобы пользователь мог начать заново
            redis_client.delete(auth_key)
            return {"status": "restart_auth", "phone_number": phone_number}
        except Exception as e:
            log.error(f"❌ Ошибка при подтверждении кода: {e}")
            log.error(f"❌ Тип ошибки: {type(e).__name__}")
            log.error(f"❌ Модуль ошибки: {e.__class__.__module__}")
            log.error(f"❌ Полное имя класса: {e.__class__.__name__}")
            redis_client.delete(auth_key)
            return {"status": "error", "error": str(e)}
        finally:
            try:
                if client.is_connected():
                    await client.disconnect()
                    log.info(f"🔌 Отключение от Telegram для {phone_number}")
            except Exception as disconnect_error:
                log.warning(f"⚠️ Ошибка при disconnect: {disconnect_error}")
    return run_async(inner)

@celery_app.task
@monitor_performance
def confirm_password_task(phone_number: str, password: str, api_id: int, api_hash: str, admin_chat_id: str = None):
    """Подтверждает пароль 2FA для Telegram аккаунта."""
    async def inner():
        session_file = get_session_file_path(phone_number)
        client = TelegramClient(session_file, api_id, api_hash)
        auth_key = f"{AUTH_STATE_KEY_PREFIX}{phone_number}"
        state_raw = redis_client.get(auth_key)
        if not state_raw:
            msg = f"Процесс авторизации для {phone_number} не запущен. Сначала запросите код."
            log.warning(msg)
            return {"status": "error", "error": msg}
        auth_state = json.loads(state_raw)
        current_status = auth_state.get("status")
        if current_status != "awaiting_password":
            msg = f"Для {phone_number} не ожидается ввод пароля. Текущий статус: {current_status}"
            log.warning(msg)
            return {"status": "error", "error": msg}
        try:
            await client.connect()
            await client.sign_in(password=password)
            
            # Явно сохраняем сессию после успешной авторизации
            session_file_full = session_file + '.session'
            log.info(f"Ожидаемый путь к файлу сессии: {session_file_full}")
            log.info(f"Файл сессии существует ДО сохранения: {os.path.exists(session_file_full)}")
            if os.path.exists(session_file_full):
                log.info(f"Размер файла ДО сохранения: {os.path.getsize(session_file_full)} байт")
            
            log.info(f"Тип сессии: {type(client.session).__name__}")
            log.info(f"Метод save доступен: {hasattr(client.session, 'save')}")
            
            # Принудительно сохраняем сессию
            try:
                if hasattr(client.session, 'save'):
                    if asyncio.iscoroutinefunction(client.session.save):
                        await client.session.save()
                        log.info("Сессия сохранена асинхронно")
                    else:
                        client.session.save()
                        log.info("Сессия сохранена синхронно")
                else:
                    # Альтернативный способ сохранения
                    await client.disconnect()
                    await client.connect()
                    log.info("Сессия сохранена через reconnect")
            except Exception as save_error:
                log.error(f"Ошибка при сохранении сессии: {save_error}")
            
            log.info(f"Файл сессии существует ПОСЛЕ сохранения: {os.path.exists(session_file_full)}")
            if os.path.exists(session_file_full):
                session_size = os.path.getsize(session_file_full)
                log.info(f"Размер файла ПОСЛЕ сохранения: {session_size} байт")
                # --- Сохраняем сессию в MongoDB ---
                existing = await get_session_by_phone(phone_number)
                if not existing:
                    session_id = str(uuid4())
                    session_data = {
                        "session_id": session_id,
                        "phone_number": phone_number,
                        "session_file_path": session_file_full,
                        "created_at": datetime.utcnow().isoformat(),
                        "channels": [],
                        "status": "active"  # Добавляем статус
                    }
                    await create_session(session_data)
                    log.info(f"Сессия сохранена в MongoDB: {session_id}")
                # ---
            else:
                log.warning(f"Сессия не сохранилась для {phone_number}")
                log.warning(f"Директория sessions существует: {os.path.exists(SESSION_DIR)}")
                log.warning(f"Права на запись в sessions: {os.access(SESSION_DIR, os.W_OK)}")
            redis_client.delete(auth_key)
            
            # Перераспределение каналов будет выполнено в боте после получения статуса
            log.info(f"✅ Авторизация {phone_number} с 2FA завершена успешно")
            
            return {"status": "confirmed", "phone_number": phone_number}
        except Exception as e:
            log.error(f"❌ Ошибка при подтверждении пароля: {e}")
            log.error(f"❌ Тип ошибки: {type(e).__name__}")
            log.error(f"❌ Модуль ошибки: {e.__class__.__module__}")
            log.error(f"❌ Полное имя класса: {e.__class__.__name__}")
            redis_client.delete(auth_key)
            return {"status": "error", "error": str(e)}
        finally:
            try:
                if client.is_connected():
                    await client.disconnect()
            except Exception as disconnect_error:
                log.warning(f"Ошибка при disconnect: {disconnect_error}")
    return run_async(inner)

@celery_app.task
@monitor_performance
def distribute_channels_task(channels: list):
    """Распределяет каналы по аккаунтам с учётом лимитов. Если channels пустой — берёт их из sources (blackbox)."""
    import asyncio
    from storage import get_sessions, update_session, create_channel_binding
    from blackbox_storage import get_all_channels, mark_channel_assigned
    
    # Проверяем, не выполняется ли уже задача
    task_key = "distribute_channels_running"
    if redis_client.get(task_key):
        log.warning("⚠️ Задача distribute_channels уже выполняется, пропускаем")
        return {"status": "already_running", "message": "Задача уже выполняется"}
    
    # Устанавливаем флаг выполнения
    redis_client.setex(task_key, 300, "1")  # 5 минут TTL
    
    async def inner():
        # Импортируем get_session_by_id здесь, чтобы избежать UnboundLocalError
        from storage import get_session_by_id
        
        # Если channels пустой — берём из sources
        channels_to_distribute = channels
        sources_map = {}  # source_id -> channel (если из БД)
        if not channels:
            sources = await get_all_channels()
            # Фильтруем только Telegram каналы
            telegram_sources = []
            for s in sources:
                source_type = s.get('type', '').lower()
                url = s.get('url', '')
                # Проверяем, что это Telegram канал
                if ('telegram' in source_type or 
                    't.me' in url or 
                    url.startswith('@') or
                    url.startswith('https://t.me/') or
                    url.startswith('http://t.me/')):
                    telegram_sources.append(s)
            
            # Для Telegram-каналов предполагаем, что url — это chat_id/username
            channels_to_distribute = [s["url"] for s in telegram_sources]
            sources_map = {s["url"]: str(s["_id"]) for s in telegram_sources}
            
            log.info(f"Найдено {len(sources)} источников, из них {len(telegram_sources)} Telegram каналов")
        
        # Получаем текущие сессии и их каналы
        sessions = await get_sessions()
        
        # Собираем все уже распределенные каналы
        distributed_channels = set()
        for session in sessions:
            distributed_channels.update(session.get('channels', []))
        
        # Фильтруем только нераспределенные каналы
        new_channels = [ch for ch in channels_to_distribute if ch not in distributed_channels]
        
        log.info(f"Всего каналов для распределения: {len(channels_to_distribute)}")
        log.info(f"Уже распределено: {len(distributed_channels)}")
        log.info(f"Новых для распределения: {len(new_channels)}")
        
        if not new_channels:
            log.info("Нет новых каналов для распределения")
            return {
                'distributed': {s['session_id']: [] for s in sessions},
                'not_loaded': [],
                'total_slots': sum(MAX_CHANNELS_PER_ACCOUNT - len(s.get('channels', [])) for s in sessions),
            }
        
        session_slots = {
            s['session_id']: MAX_CHANNELS_PER_ACCOUNT - len(s.get('channels', []))
            for s in sessions
        }
        distributed = {s['session_id']: [] for s in sessions}
        not_loaded = []
        session_id_list = list(session_slots.keys())
        idx = 0
        
        for channel in new_channels:
            placed = False
            for _ in range(len(session_id_list)):
                sid = session_id_list[idx % len(session_id_list)]
                if session_slots[sid] > 0:
                    await create_channel_binding({"session_id": sid, "chat_id": channel})
                    
                    # Получаем актуальные каналы из базы данных для этой сессии
                    from storage import get_session_by_id
                    try:
                        # Пытаемся получить сессию по ID
                        target_session = await get_session_by_id(sid)
                        if target_session:
                            current_channels = target_session.get('channels', [])
                        else:
                            # Если не удалось получить, начинаем с пустого списка
                            current_channels = []
                            log.warning(f"⚠️ Не удалось получить сессию {sid} из базы данных")
                    except Exception as e:
                        log.warning(f"⚠️ Ошибка при получении сессии {sid}: {e}")
                        current_channels = []
                    
                    # Проверяем, нет ли уже такого канала
                    if channel in current_channels:
                        log.warning(f"⚠️ Канал {channel} уже существует в сессии {sid}, пропускаем")
                        continue
                    
                    # Добавляем новый канал
                    current_channels.append(channel)
                    
                    # Обновляем сессию в базе данных
                    result = await update_session(sid, {"channels": current_channels})
                    
                    # Проверяем, что обновление прошло успешно
                    if result.modified_count > 0:
                        log.info(f"✅ Канал {channel} успешно добавлен в сессию {sid}")
                    else:
                        log.warning(f"⚠️ Канал {channel} не был добавлен в сессию {sid}")
                    
                    session_slots[sid] -= 1
                    distributed[sid].append(channel)
                    
                    # Если канал из sources — обновляем статус
                    if channel in sources_map:
                        await mark_channel_assigned(sources_map[channel], sid)
                    placed = True
                    idx += 1
                    break
                idx += 1
            if not placed:
                not_loaded.append(channel)
        
        total_slots = sum(session_slots.values())
        return {
            'distributed': distributed,
            'not_loaded': not_loaded,
            'total_slots': total_slots,
        }
    
    # Очищаем флаг выполнения
    redis_client.delete(task_key)
    return run_async(inner)

@celery_app.task
@monitor_performance
def check_session_status_task(phone_number: str, api_id: int, api_hash: str):
    """Проверяет статус сессии Telegram аккаунта и обновляет его в MongoDB."""
    async def inner():
        from storage import update_session_by_phone
        session_file = get_session_file_path(phone_number)  # без .session
        session_file_full = session_file + '.session'
        log.info(f"Путь к файлу сессии (для Telethon): {session_file}")
        log.info(f"Файл сессии на диске: {session_file_full}")
        log.info(f"API_ID: {api_id}, API_HASH: {api_hash}")
        log.info(f"Файл существует: {os.path.exists(session_file_full)}")
        client = TelegramClient(session_file, api_id, api_hash)
        try:
            await client.connect()
            is_authorized = await client.is_user_authorized()
            log.info(f"is_user_authorized: {is_authorized}")
            status = "active" if is_authorized else "inactive"
            log.info(f"Статус сессии {phone_number}: {status}")
            # Обновляем статус в MongoDB
            await update_session_by_phone(phone_number, {"status": status})
            return {"status": status, "phone_number": phone_number}
        except Exception as e:
            log.error(f"Ошибка при проверке статуса сессии {phone_number}: {e}")
            # Если ошибка — помечаем как неактивную
            await update_session_by_phone(phone_number, {"status": "inactive"})
            return {"status": "error", "phone_number": phone_number, "error": str(e)}
        finally:
            try:
                if client.is_connected():
                    await client.disconnect()
            except Exception as disconnect_error:
                log.warning(f"Ошибка при disconnect: {disconnect_error}")
    return run_async(inner)

@celery_app.task
@monitor_performance
def check_all_sessions_status_task():
    """Проверяет статус всех сессий и обновляет их в MongoDB."""
    async def inner():
        from storage import get_sessions, update_session_by_phone
        sessions = await get_sessions()
        results = []
        for session in sessions:
            phone_number = session.get("phone_number")
            if not phone_number:
                continue
            api_id = API_ID
            api_hash = API_HASH
            session_file = get_session_file_path(phone_number)
            session_file_full = session_file + '.session'
            log.info(f"Путь к файлу сессии (для Telethon): {session_file}")
            log.info(f"Файл сессии на диске: {session_file_full}")
            log.info(f"API_ID: {api_id}, API_HASH: {api_hash}")
            log.info(f"Файл существует: {os.path.exists(session_file_full)}")
            client = TelegramClient(session_file, api_id, api_hash)
            try:
                await client.connect()
                
                # Дополнительная диагностика
                try:
                    me = await client.get_me()
                    log.info(f"Получен пользователь: {me.first_name} {me.last_name} (@{me.username})")
                except Exception as me_error:
                    log.warning(f"Не удалось получить информацию о пользователе: {me_error}")
                
                is_authorized = await client.is_user_authorized()
                log.info(f"is_user_authorized: {is_authorized}")
                
                # Проверяем размер файла сессии
                if os.path.exists(session_file_full):
                    session_size = os.path.getsize(session_file_full)
                    log.info(f"Размер файла сессии: {session_size} байт")
                
                status = "active" if is_authorized else "inactive"
                log.info(f"Статус сессии {phone_number}: {status}")
                await update_session_by_phone(phone_number, {"status": status})
                results.append({"status": status, "phone_number": phone_number})
            except Exception as e:
                log.error(f"Ошибка при проверке статуса сессии {phone_number}: {e}")
                await update_session_by_phone(phone_number, {"status": "inactive"})
                results.append({"status": "error", "phone_number": phone_number, "error": str(e)})
            finally:
                try:
                    if client.is_connected():
                        await client.disconnect()
                except Exception as disconnect_error:
                    log.warning(f"Ошибка при disconnect: {disconnect_error}")
        return {"results": results}
    return run_async(inner) 

@celery_app.task
@monitor_performance
def clean_duplicate_channels_task():
    """Очищает дубликаты каналов в сессиях"""
    import asyncio
    from storage import get_sessions, update_session
    async def inner():
        sessions = await get_sessions()
        cleaned_count = 0
        
        for session in sessions:
            channels = session.get('channels', [])
            if channels:
                # Удаляем дубликаты, сохраняя порядок
                unique_channels = []
                seen = set()
                for ch in channels:
                    if ch not in seen:
                        unique_channels.append(ch)
                        seen.add(ch)
                
                # Если были дубликаты, обновляем сессию
                if len(unique_channels) != len(channels):
                    result = await update_session(session['session_id'], {"channels": unique_channels})
                    if result.modified_count > 0:
                        cleaned_count += len(channels) - len(unique_channels)
                        log.info(f"Очищено {len(channels) - len(unique_channels)} дубликатов в сессии {session['session_id']}")
                    else:
                        log.warning(f"⚠️ Не удалось обновить сессию {session['session_id']} при очистке дубликатов")
        
        log.info(f"Всего очищено {cleaned_count} дубликатов")
        
        # Дополнительная проверка: получаем актуальные данные из базы данных
        log.info("🔍 Проверяем актуальные данные после очистки дубликатов...")
        updated_sessions = await get_sessions()
        for session in updated_sessions:
            phone = session.get('phone_number', 'Unknown')
            actual_channels = session.get('channels', [])
            log.info(f"   📱 {phone}: {len(actual_channels)} каналов")
        
        return {"cleaned_duplicates": cleaned_count}
    return run_async(inner)

@celery_app.task
@monitor_performance
def clear_all_channels_from_sessions_task():
    """Очищает все каналы из всех сессий и сбрасывает привязки в blackbox_db"""
    async def inner():
        try:
            log.info("🧹 Начинаем очистку всех каналов из сессий")
            
            # Получаем все сессии
            sessions_collection = db["sessions"]
            sessions = await sessions_collection.find({}).to_list(length=None)
            
            cleared_count = 0
            for session in sessions:
                phone_number = session.get("phone_number")
                if phone_number:
                    # Очищаем каналы в сессии
                    await sessions_collection.update_one(
                        {"phone_number": phone_number},
                        {"$set": {"channels": []}}
                    )
                    cleared_count += 1
                    log.info(f"🧹 Очищены каналы для сессии {phone_number}")
            
            # Сбрасываем привязки в blackbox_db
            sources_collection = blackbox_db["sources"]
            await sources_collection.update_many(
                {},
                {"$unset": {"session_id": "", "assigned_at": ""}}
            )
            
            log.info(f"✅ Очищено {cleared_count} сессий, сброшены привязки в blackbox_db")
            send_admin_notification(f"✅ Очищено {cleared_count} сессий, сброшены привязки в blackbox_db")
            
        except Exception as e:
            error_msg = f"❌ Ошибка при очистке каналов: {e}"
            log.error(error_msg)
            send_admin_notification(error_msg)
            raise
    
    return run_async(inner)

@celery_app.task
@monitor_performance
def delete_session_and_redistribute_task(phone_number: str):
    """Удаляет сессию и перераспределяет её каналы по другим сессиям"""
    async def inner():
        try:
            log.info(f"🗑️ Начинаем удаление сессии {phone_number} с перераспределением каналов")
            
            # Получаем сессию для удаления
            sessions_collection = db["sessions"]
            session = await sessions_collection.find_one({"phone_number": phone_number})
            
            if not session:
                error_msg = f"❌ Сессия {phone_number} не найдена"
                log.error(error_msg)
                send_admin_notification(error_msg)
                return
            
            # Получаем каналы удаляемой сессии
            channels_to_redistribute = session.get("channels", [])
            log.info(f"📋 Найдено {len(channels_to_redistribute)} каналов для перераспределения")
            
            # Удаляем сессию из MongoDB
            await sessions_collection.delete_one({"phone_number": phone_number})
            log.info(f"🗑️ Удалена сессия {phone_number} из MongoDB")
            
            # Удаляем файл сессии
            if session_exists(phone_number):
                remove_session(phone_number)
                log.info(f"🗑️ Удален файл сессии {phone_number}")
            
            # Сбрасываем привязки каналов в blackbox_db
            sources_collection = blackbox_db["sources"]
            for channel in channels_to_redistribute:
                await sources_collection.update_many(
                    {"url": channel},
                    {"$unset": {"session_id": "", "assigned_at": ""}}
                )
            
            log.info(f"🔄 Сброшены привязки для {len(channels_to_redistribute)} каналов")
            
            # Перераспределяем каналы по оставшимся сессиям
            if channels_to_redistribute:
                # Получаем все активные сессии
                active_sessions = await sessions_collection.find({}).to_list(length=None)
                
                if active_sessions:
                    # Используем новую логику равномерного распределения
                    session_id_list = [s["session_id"] for s in active_sessions]
                    
                    # Распределяем каналы равномерно по активным сессиям
                    for i, channel in enumerate(channels_to_redistribute):
                        target_session_id = session_id_list[i % len(session_id_list)]
                        target_session = next(s for s in active_sessions if s["session_id"] == target_session_id)
                        target_phone = target_session["phone_number"]
                        
                        # Добавляем канал к целевой сессии
                        await sessions_collection.update_one(
                            {"phone_number": target_phone},
                            {"$push": {"channels": channel}}
                        )
                        
                        # Обновляем привязку в blackbox_db
                        await sources_collection.update_many(
                            {"url": channel},
                            {
                                "$set": {
                                    "session_id": target_session_id,
                                    "assigned_at": datetime.utcnow()
                                }
                            }
                        )
                        
                        log.info(f"✅ Канал {channel} перераспределен в сессию {target_phone}")
                    
                    log.info(f"✅ Перераспределено {len(channels_to_redistribute)} каналов по {len(active_sessions)} сессиям")
                    send_admin_notification(f"✅ Удалена сессия {phone_number}, перераспределено {len(channels_to_redistribute)} каналов")
                else:
                    log.warning("⚠️ Нет активных сессий для перераспределения каналов")
                    send_admin_notification(f"⚠️ Удалена сессия {phone_number}, но нет активных сессий для перераспределения каналов")
                    
                    # Если каналы не были перераспределены, сбрасываем их привязки
                    if channels_to_redistribute:
                        log.info(f"🔄 Сбрасываем привязки для {len(channels_to_redistribute)} каналов (нет активных сессий)")
                        for channel in channels_to_redistribute:
                            await sources_collection.update_many(
                                {"url": channel},
                                {"$unset": {"session_id": "", "assigned_at": ""}}
                            )
                        send_admin_notification(f"🔄 Сброшены привязки для {len(channels_to_redistribute)} каналов (нет активных сессий)")
            else:
                log.info(f"✅ Удалена сессия {phone_number} (каналов для перераспределения не было)")
                send_admin_notification(f"✅ Удалена сессия {phone_number}")
            
        except Exception as e:
            error_msg = f"❌ Ошибка при удалении сессии {phone_number}: {e}"
            log.error(error_msg)
            send_admin_notification(error_msg)
            raise
    
    return run_async(inner) 

@celery_app.task
@monitor_performance
def redistribute_all_channels_task():
    """Полностью перераспределяет все каналы по всем доступным сессиям"""
    import asyncio
    from storage import get_sessions, update_session, create_channel_binding
    from blackbox_storage import get_all_channels, mark_channel_assigned
    
    # Проверяем, не выполняется ли уже задача
    task_key = "redistribute_all_channels_running"
    if redis_client.get(task_key):
        log.warning("⚠️ Задача redistribute_all_channels уже выполняется, пропускаем")
        return {"status": "already_running", "message": "Задача уже выполняется"}
    
    # Устанавливаем флаг выполнения
    redis_client.setex(task_key, 300, "1")  # 5 минут TTL
    
    async def inner():
        try:
            log.info("🔄 Начинаем полное перераспределение всех каналов")
            
            # Импортируем get_session_by_id здесь, чтобы избежать UnboundLocalError
            from storage import get_session_by_id
            
            # Получаем все источники
            sources = await get_all_channels()
            # Фильтруем только Telegram каналы
            telegram_sources = []
            for s in sources:
                source_type = s.get('type', '').lower()
                url = s.get('url', '')
                # Проверяем, что это Telegram канал
                if ('telegram' in source_type or 
                    't.me' in url or 
                    url.startswith('@') or
                    url.startswith('https://t.me/') or
                    url.startswith('http://t.me/')):
                    telegram_sources.append(s)
            
            # Для Telegram-каналов предполагаем, что url — это chat_id/username
            all_channels = [s["url"] for s in telegram_sources]
            sources_map = {s["url"]: str(s["_id"]) for s in telegram_sources}
            
            log.info(f"Найдено {len(sources)} источников, из них {len(telegram_sources)} Telegram каналов")
            log.info(f"Всего каналов для перераспределения: {len(all_channels)}")
            
            # Получаем все сессии
            sessions = await get_sessions()
            if not sessions:
                log.warning("⚠️ Нет доступных сессий для перераспределения")
                return {
                    'distributed': {},
                    'not_loaded': all_channels,
                    'total_slots': 0,
                }
            
            # Очищаем все каналы из всех сессий
            for session in sessions:
                result = await update_session(session['session_id'], {"channels": []})
                if result.modified_count > 0:
                    log.info(f"🧹 Очищены каналы из сессии {session['phone_number']}")
                else:
                    log.warning(f"⚠️ Не удалось очистить каналы из сессии {session['phone_number']}")
            
            # Сбрасываем все привязки в blackbox_db
            sources_collection = blackbox_db["sources"]
            await sources_collection.update_many(
                {},
                {"$unset": {"session_id": "", "assigned_at": ""}}
            )
            log.info("🧹 Сброшены все привязки каналов в blackbox_db")
            
            # Дополнительная проверка: убеждаемся, что каналы действительно очищены
            log.info("🔍 Проверяем, что каналы действительно очищены...")
            for session in sessions:
                updated_session = await get_session_by_id(session['session_id'])
                if updated_session:
                    actual_channels = updated_session.get('channels', [])
                    if actual_channels:
                        log.warning(f"⚠️ Сессия {session['phone_number']} все еще содержит каналы: {actual_channels}")
                    else:
                        log.info(f"✅ Сессия {session['phone_number']} успешно очищена")
            
            # Распределяем все каналы заново равномерно
            session_slots = {
                s['session_id']: MAX_CHANNELS_PER_ACCOUNT
                for s in sessions
            }
            distributed = {s['session_id']: [] for s in sessions}
            not_loaded = []
            session_id_list = list(session_slots.keys())
            
            # Распределяем каналы равномерно по сессиям
            for i, channel in enumerate(all_channels):
                # Выбираем сессию по кругу для равномерного распределения
                target_session_id = session_id_list[i % len(session_id_list)]
                
                if session_slots[target_session_id] > 0:
                    await create_channel_binding({"session_id": target_session_id, "chat_id": channel})
                    
                    # Получаем актуальные каналы из базы данных для этой сессии
                    from storage import get_session_by_id
                    try:
                        # Пытаемся получить сессию по ID
                        target_session = await get_session_by_id(target_session_id)
                        if target_session:
                            current_channels = target_session.get('channels', [])
                        else:
                            # Если не удалось получить, начинаем с пустого списка
                            current_channels = []
                            log.warning(f"⚠️ Не удалось получить сессию {target_session_id} из базы данных")
                    except Exception as e:
                        log.warning(f"⚠️ Ошибка при получении сессии {target_session_id}: {e}")
                        current_channels = []
                    
                    # Проверяем, нет ли уже такого канала
                    if channel in current_channels:
                        log.warning(f"⚠️ Канал {channel} уже существует в сессии {target_session_id}, пропускаем")
                        continue
                    
                    # Добавляем новый канал
                    current_channels.append(channel)
                    
                    # Обновляем сессию в базе данных
                    result = await update_session(target_session_id, {"channels": current_channels})
                    
                    # Проверяем, что обновление прошло успешно
                    if result.modified_count > 0:
                        log.info(f"✅ Канал {channel} успешно добавлен в сессию {target_session_id}")
                    else:
                        log.warning(f"⚠️ Канал {channel} не был добавлен в сессию {target_session_id}")
                    
                    session_slots[target_session_id] -= 1
                    distributed[target_session_id].append(channel)
                    
                    # Если канал из sources — обновляем статус
                    if channel in sources_map:
                        await mark_channel_assigned(sources_map[channel], target_session_id)
                    log.info(f"✅ Канал {channel} размещен в сессии {target_session_id}")
                else:
                    not_loaded.append(channel)
                    log.warning(f"⚠️ Не удалось разместить канал {channel} - нет свободных слотов")
            
            # Логируем результаты
            total_distributed = sum(len(channels) for channels in distributed.values())
            log.info(f"✅ Перераспределение завершено:")
            log.info(f"   📊 Всего каналов: {len(all_channels)}")
            log.info(f"   ✅ Распределено: {total_distributed}")
            log.info(f"   ❌ Не размещено: {len(not_loaded)}")
            
            for session_id, channels in distributed.items():
                session = next(s for s in sessions if s['session_id'] == session_id)
                phone = session['phone_number']
                log.info(f"   📱 {phone}: {len(channels)} каналов")
            
            # Дополнительная проверка: получаем актуальные данные из базы данных
            log.info("🔍 Проверяем актуальные данные в базе данных...")
            updated_sessions = await get_sessions()
            for session in updated_sessions:
                phone = session.get('phone_number', 'Unknown')
                actual_channels = session.get('channels', [])
                expected_channels = distributed.get(session['session_id'], [])
                log.info(f"   📱 {phone}: ожидается {len(expected_channels)}, фактически {len(actual_channels)} каналов")
                if len(actual_channels) != len(expected_channels):
                    log.warning(f"   ⚠️ Несоответствие для {phone}: ожидается {len(expected_channels)}, фактически {len(actual_channels)}")
                    log.warning(f"   📋 Ожидаемые каналы: {expected_channels}")
                    log.warning(f"   📋 Фактические каналы: {actual_channels}")
                    
                    # Попытка исправить несоответствие
                    if len(actual_channels) == 0 and len(expected_channels) > 0:
                        log.info(f"   🔧 Попытка исправить несоответствие для {phone}...")
                        try:
                            result = await update_session(session['session_id'], {"channels": expected_channels})
                            if result.modified_count > 0:
                                log.info(f"   ✅ Несоответствие исправлено для {phone}")
                            else:
                                log.warning(f"   ❌ Не удалось исправить несоответствие для {phone}")
                        except Exception as e:
                            log.error(f"   ❌ Ошибка при исправлении несоответствия для {phone}: {e}")
                else:
                    log.info(f"   ✅ {phone}: каналы распределены корректно")
                    
                    # Проверяем на дубликаты
                    if len(actual_channels) != len(set(actual_channels)):
                        log.warning(f"   ⚠️ Обнаружены дубликаты в {phone}: {actual_channels}")
                    else:
                        log.info(f"   ✅ {phone}: дубликатов не обнаружено")
            
            # Финальная проверка: убеждаемся, что все каналы сохранены
            log.info("🔍 Финальная проверка сохранения каналов...")
            final_sessions = await get_sessions()
            total_saved_channels = sum(len(s.get('channels', [])) for s in final_sessions)
            total_expected_channels = sum(len(channels) for channels in distributed.values())
            
            if total_saved_channels == total_expected_channels:
                log.info(f"✅ Все каналы успешно сохранены: {total_saved_channels}")
            else:
                log.warning(f"⚠️ Несоответствие в количестве сохраненных каналов: ожидается {total_expected_channels}, фактически {total_saved_channels}")
            
            return {
                'distributed': distributed,
                'not_loaded': not_loaded,
                'total_slots': sum(session_slots.values()),
                'total_saved_channels': total_saved_channels,
                'total_expected_channels': total_expected_channels,
            }
            
        except Exception as e:
            log.error(f"❌ Ошибка при полном перераспределении каналов: {e}")
            raise
        finally:
            # Очищаем флаг выполнения
            redis_client.delete(task_key)
    
    return run_async(inner) 