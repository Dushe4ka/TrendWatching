from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from models import (
    RequestCodeModel, ConfirmCodeModel, StatusResponse, SessionStatusRequest, 
    RemoveSessionRequest, SessionInfo, DistributeChannelsRequest, DistributeChannelsResult, 
    ConfirmPasswordModel, ParseSourcesRequest, ParseRSSRequest, ParseTelegramRequest, 
    ParseSpecificSourceRequest, ParsingResult
)
from celery_app.auth_tasks import (
    request_code_task, confirm_code_task, distribute_channels_task, confirm_password_task, 
    check_session_status_task, check_all_sessions_status_task
)
from celery_app.parsing_tasks import (
    parse_sources_task, parse_rss_sources_task, parse_telegram_sources_task, parse_specific_source_task
)
from storage import get_sessions
from config import MAX_CHANNELS_PER_ACCOUNT
from session_manager import get_session_file_path, remove_session, session_exists
import os

app = FastAPI(title="TG Auth Service")

@app.post("/auth/request_code")
def request_code(data: RequestCodeModel):
    task = request_code_task.delay(
        data.phone_number,
        data.api_id,
        data.api_hash,
        data.admin_chat_id
    )
    # Ждем результат задачи
    result = task.get(timeout=30)
    return result

@app.post("/auth/confirm_code")
def confirm_code(data: ConfirmCodeModel):
    task = confirm_code_task.delay(
        data.phone_number,
        data.code,
        data.api_id,
        data.api_hash,
        data.admin_chat_id
    )
    # Ждем результат задачи
    result = task.get(timeout=30)
    return result

@app.post("/auth/distribute_channels", response_model=dict)
def distribute_channels(data: DistributeChannelsRequest):
    task = distribute_channels_task.delay(data.channels)
    return {"task_id": task.id, "status": "distribution_started"}

@app.post("/auth/distribute_channels_from_db", response_model=dict)
def distribute_channels_from_db():
    task = distribute_channels_task.delay([])  # Пустой список — значит брать из БД
    return {"task_id": task.id, "status": "distribution_from_db_started"}

@app.post("/auth/redistribute_all_channels", response_model=dict)
def redistribute_all_channels():
    """Полностью перераспределяет все каналы по всем доступным сессиям"""
    from celery_app.auth_tasks import redistribute_all_channels_task
    task = redistribute_all_channels_task.delay()
    return {"task_id": task.id, "status": "redistribution_started"}

@app.get("/auth/task_status/{task_id}", response_model=dict)
def get_task_status(task_id: str):
    """Получает статус задачи Celery"""
    from celery_app.auth_tasks import celery_app
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }

@app.post("/auth/clean_duplicate_channels", response_model=dict)
def clean_duplicate_channels():
    """Очищает дубликаты каналов в сессиях"""
    from celery_app.auth_tasks import clean_duplicate_channels_task
    task = clean_duplicate_channels_task.delay()
    return {"task_id": task.id, "status": "clean_duplicates_started"}

@app.post("/auth/clear_all_channels", response_model=dict)
def clear_all_channels():
    """Очищает все каналы из всех сессий"""
    from celery_app.auth_tasks import clear_all_channels_from_sessions_task
    task = clear_all_channels_from_sessions_task.delay()
    return {"task_id": task.id, "status": "clear_all_channels_started"}

@app.post("/auth/confirm_password")
def confirm_password(data: ConfirmPasswordModel):
    task = confirm_password_task.delay(
        data.phone_number,
        data.password,
        data.api_id,
        data.api_hash,
        data.admin_chat_id
    )
    # Ждем результат задачи
    result = task.get(timeout=30)
    return result

@app.get("/auth/status", response_model=StatusResponse)
async def status():
    """Получает статус авторизации с информацией только о Telegram каналах"""
    from blackbox_storage import get_all_channels
    
    sessions = await get_sessions()
    total_accounts = len(sessions)
    
    # Получаем все источники и фильтруем только Telegram каналы
    sources = await get_all_channels()
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
    
    # Подсчитываем только Telegram каналы
    total_telegram_channels = len(telegram_sources)
    total_assigned_channels = sum(len(s.get("channels", [])) for s in sessions)
    available_slots = total_accounts * MAX_CHANNELS_PER_ACCOUNT - total_assigned_channels
    
    return StatusResponse(
        total_accounts=total_accounts,
        total_channels=total_telegram_channels,  # Показываем только Telegram каналы
        max_channels_per_account=MAX_CHANNELS_PER_ACCOUNT,
        available_slots=available_slots,
        sessions=[
            {
                "session_id": s.get("session_id", ""),
                "phone_number": s.get("phone_number", ""),
                "channels": s.get("channels", []),
                "created_at": str(s.get("created_at", "")),
                "session_file_path": s.get("session_file_path", "")
            } for s in sessions
        ]
    )

@app.get("/auth/status_full", response_model=StatusResponse)
async def status_full():
    """Получает полный статус авторизации со всеми источниками"""
    from blackbox_storage import get_all_channels
    
    sessions = await get_sessions()
    total_accounts = len(sessions)
    
    # Получаем все источники
    sources = await get_all_channels()
    total_all_sources = len(sources)
    total_assigned_channels = sum(len(s.get("channels", [])) for s in sessions)
    available_slots = total_accounts * MAX_CHANNELS_PER_ACCOUNT - total_assigned_channels
    
    return StatusResponse(
        total_accounts=total_accounts,
        total_channels=total_all_sources,  # Показываем все источники
        max_channels_per_account=MAX_CHANNELS_PER_ACCOUNT,
        available_slots=available_slots,
        sessions=[
            {
                "session_id": s.get("session_id", ""),
                "phone_number": s.get("phone_number", ""),
                "channels": s.get("channels", []),
                "created_at": str(s.get("created_at", "")),
                "session_file_path": s.get("session_file_path", "")
            } for s in sessions
        ]
    )

@app.get("/auth/session_status", response_model=SessionInfo)
async def session_status(phone_number: str = Query(..., examples=["+79991234567"])):
    sessions = await get_sessions()
    # Исправляем номер телефона: заменяем пробел в начале на плюс
    if phone_number.startswith(' '):
        phone_number = '+' + phone_number[1:]
    # Отладочная информация
    print(f"DEBUG: Ищем номер: '{phone_number}'")
    print(f"DEBUG: Всего сессий: {len(sessions)}")
    for i, s in enumerate(sessions):
        print(f"DEBUG: Сессия {i}: phone_number='{s.get('phone_number')}', тип={type(s.get('phone_number'))}")
    for s in sessions:
        if s.get("phone_number") == phone_number:
            return SessionInfo(
                session_id=s.get("session_id", ""),
                phone_number=s.get("phone_number", ""),
                channels=s.get("channels", []),
                created_at=str(s.get("created_at", "")),
                session_file_path=s.get("session_file_path", "")
            )
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/auth/remove_session")
def remove_session_endpoint(data: RemoveSessionRequest):
    phone_number = data.phone_number
    if not session_exists(phone_number):
        raise HTTPException(status_code=404, detail="Session file not found")
    remove_session(phone_number)
    return {"status": "removed", "phone_number": phone_number}

@app.delete("/auth/delete_session")
def delete_session_endpoint(data: RemoveSessionRequest):
    """Удаляет сессию и перераспределяет каналы"""
    from celery_app.auth_tasks import delete_session_and_redistribute_task
    
    phone_number = data.phone_number
    if not session_exists(phone_number):
        raise HTTPException(status_code=404, detail="Session file not found")
    
    # Запускаем задачу удаления сессии с перераспределением
    task = delete_session_and_redistribute_task.delay(phone_number)
    return {"task_id": task.id, "status": "delete_and_redistribute_started", "phone_number": phone_number}

@app.get("/auth/debug_sessions")
async def debug_sessions():
    """Отладочный эндпоинт для просмотра всех сессий в MongoDB."""
    from bson import ObjectId
    sessions = await get_sessions()
    # Конвертируем ObjectId в строку для JSON сериализации
    serialized_sessions = []
    for session in sessions:
        session_copy = session.copy()
        if '_id' in session_copy:
            session_copy['_id'] = str(session_copy['_id'])
        serialized_sessions.append(session_copy)
    return {
        "total_sessions": len(serialized_sessions),
        "sessions": serialized_sessions
    }

@app.get("/auth/check_status")
def check_status(phone_number: str = Query(..., examples=["+79991234567"]), api_id: int = Query(..., examples=[123456]), api_hash: str = Query(..., examples=["your_api_hash"])):
    """Проверяет статус сессии для одного номера."""
    # Исправляем номер телефона
    if phone_number.startswith(' '):
        phone_number = '+' + phone_number[1:]
    task = check_session_status_task.delay(phone_number, api_id, api_hash)
    return {"task_id": task.id, "status": "check_started", "phone_number": phone_number}

@app.post("/auth/check_all_status")
def check_all_status():
    """Проверяет статус всех сессий."""
    task = check_all_sessions_status_task.delay()
    return {"task_id": task.id, "status": "check_all_started"}

@app.post("/parsing/parse_all_sources", response_model=ParsingResult)
def parse_all_sources(data: ParseSourcesRequest):
    """Запускает парсинг всех источников (RSS + Telegram)"""
    try:
        # Если limit не указан, используем None для парсинга всех источников
        limit = data.limit if data.limit is not None else None
        task = parse_sources_task.delay(limit, data.chat_id)
        return ParsingResult(
            task_id=task.id,
            status="parsing_started",
            message=f"Парсинг всех источников запущен (лимит: {limit if limit else 'все'})"
        )
    except Exception as e:
        print(f"DEBUG: Error submitting task: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/parsing/parse_rss_sources", response_model=ParsingResult)
def parse_rss_sources(data: ParseRSSRequest):
    """Запускает парсинг только RSS источников"""
    limit = data.limit if data.limit is not None else None
    task = parse_rss_sources_task.delay(limit, data.chat_id)
    return ParsingResult(
        task_id=task.id,
        status="rss_parsing_started",
        message=f"Парсинг RSS источников запущен (лимит: {limit if limit else 'все'})"
    )

@app.post("/parsing/parse_telegram_sources", response_model=ParsingResult)
def parse_telegram_sources(data: ParseTelegramRequest):
    """Запускает парсинг только Telegram источников"""
    limit = data.limit if data.limit is not None else None
    task = parse_telegram_sources_task.delay(limit, data.chat_id)
    return ParsingResult(
        task_id=task.id,
        status="telegram_parsing_started",
        message=f"Парсинг Telegram источников запущен (лимит: {limit if limit else 'все'})"
    )

@app.post("/parsing/parse_specific_source", response_model=ParsingResult)
def parse_specific_source(data: ParseSpecificSourceRequest):
    """Запускает парсинг конкретного источника"""
    task = parse_specific_source_task.delay(data.source_url, data.source_type, data.chat_id)
    return ParsingResult(
        task_id=task.id,
        status="specific_parsing_started",
        message=f"Парсинг источника {data.source_url} запущен (тип: {data.source_type})"
    )

@app.get("/parsing/status")
async def parsing_status():
    """Получает статус парсинга и статистику"""
    try:
        from blackbox_storage import get_new_channels
        from parsers.source_parser import SourceParser
        from storage import db
        from blackbox_storage import blackbox_db
        
        # Инициализируем парсер для получения статистики
        parsed_data_collection = db["parsed_data"]
        parser = SourceParser(parsed_data_collection, blackbox_db)
        
        # Получаем статистику
        sources = await parser.get_available_sources(limit=1000)
        sessions = await parser.get_active_sessions()
        categorized = parser.categorize_sources(sources)
        
        # Получаем количество спарсенных записей (асинхронно)
        total_parsed = await parsed_data_collection.count_documents({})
        rss_parsed = await parsed_data_collection.count_documents({"source_type": "rss"})
        telegram_parsed = await parsed_data_collection.count_documents({"source_type": "telegram"})
        
        # Убеждаемся, что все значения являются простыми типами
        # Проверяем, что sources и sessions являются списками, а не Future
        sources_len = len(sources) if isinstance(sources, list) else 0
        sessions_len = len(sessions) if isinstance(sessions, list) else 0
        
        return {
            "total_sources": int(sources_len),
            "rss_sources": int(len(categorized.get('rss', []))),
            "telegram_sources": int(len(categorized.get('telegram', []))),
            "active_sessions": int(sessions_len),
            "total_parsed_records": int(total_parsed),
            "rss_parsed_records": int(rss_parsed),
            "telegram_parsed_records": int(telegram_parsed)
        }
        
    except Exception as e:
        print(f"ERROR in parsing_status: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статуса: {str(e)}")

@app.get("/auth/check_auth_state")
def check_auth_state(phone_number: str = Query(..., examples=["+79991234567"])):
    """Проверяет состояние авторизации в Redis для указанного номера"""
    try:
        import redis
        import json
        
        # Redis клиент
        REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
        REDIS_DB = int(os.getenv('REDIS_DB', 0))
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        
        auth_key = f"telegram_auth_state:{phone_number}"
        state_raw = redis_client.get(auth_key)
        
        if not state_raw:
            return {
                "phone_number": phone_number,
                "has_state": False,
                "message": "Состояние авторизации не найдено"
            }
        
        auth_state = json.loads(state_raw)
        ttl = redis_client.ttl(auth_key)
        
        return {
            "phone_number": phone_number,
            "has_state": True,
            "state": auth_state,
            "ttl_seconds": ttl,
            "ttl_minutes": ttl // 60 if ttl > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при проверке состояния: {str(e)}")

@app.post("/auth/clear_auth_state")
def clear_auth_state(phone_number: str = Query(..., examples=["+79991234567"])):
    """Очищает состояние авторизации в Redis для указанного номера"""
    try:
        import redis
        
        # Redis клиент
        REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
        REDIS_DB = int(os.getenv('REDIS_DB', 0))
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        
        auth_key = f"telegram_auth_state:{phone_number}"
        deleted = redis_client.delete(auth_key)
        
        return {
            "phone_number": phone_number,
            "deleted": deleted > 0,
            "message": "Состояние авторизации очищено" if deleted > 0 else "Состояние не найдено"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке состояния: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 