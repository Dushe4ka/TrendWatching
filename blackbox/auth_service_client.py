import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv
import os
from logger_config import setup_logger

load_dotenv()

# Настраиваем логгер
logger = setup_logger("auth_service_client")

class AuthServiceClient:
    """Клиент для взаимодействия с микросервисом auth_tg_service"""
    
    def __init__(self):
        self.base_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")
        self.timeout = 30
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Выполняет HTTP запрос к микросервису"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(
                method=method,
                url=url,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка {response.status_code} при запросе к {url}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при запросе к микросервису: {e}")
            return None
    
    # Методы для авторизации
    def request_code(self, phone_number: str, api_id: int, api_hash: str, admin_chat_id: str = None) -> Optional[Dict]:
        """Запрашивает код авторизации"""
        data = {
            "phone_number": phone_number,
            "api_id": api_id,
            "api_hash": api_hash
        }
        if admin_chat_id:
            data["admin_chat_id"] = admin_chat_id
        
        return self._make_request("POST", "/auth/request_code", data)
    
    def confirm_code(self, phone_number: str, code: str, api_id: int, api_hash: str, admin_chat_id: str = None) -> Optional[Dict]:
        """Подтверждает код авторизации"""
        data = {
            "phone_number": phone_number,
            "code": code,
            "api_id": api_id,
            "api_hash": api_hash
        }
        if admin_chat_id:
            data["admin_chat_id"] = admin_chat_id
        
        return self._make_request("POST", "/auth/confirm_code", data)
    
    def confirm_password(self, phone_number: str, password: str, api_id: int, api_hash: str, admin_chat_id: str = None) -> Optional[Dict]:
        """Подтверждает пароль 2FA"""
        data = {
            "phone_number": phone_number,
            "password": password,
            "api_id": api_id,
            "api_hash": api_hash
        }
        if admin_chat_id:
            data["admin_chat_id"] = admin_chat_id
        
        return self._make_request("POST", "/auth/confirm_password", data)
    
    # Методы для управления сессиями
    def get_status(self) -> Optional[Dict]:
        """Получает статус всех сессий"""
        return self._make_request("GET", "/auth/status")
    
    def get_session_status(self, phone_number: str) -> Optional[Dict]:
        """Получает статус конкретной сессии"""
        return self._make_request("GET", f"/auth/session_status?phone_number={phone_number}")
    
    def remove_session(self, phone_number: str) -> Optional[Dict]:
        """Удаляет сессию"""
        return self._make_request("POST", "/auth/remove_session", {"phone_number": phone_number})
    
    def check_session_status(self, phone_number: str, api_id: int, api_hash: str) -> Optional[Dict]:
        """Проверяет статус сессии"""
        return self._make_request("GET", f"/auth/check_status?phone_number={phone_number}&api_id={api_id}&api_hash={api_hash}")
    
    def check_all_sessions_status(self) -> Optional[Dict]:
        """Проверяет статус всех сессий"""
        return self._make_request("POST", "/auth/check_all_status")
    
    # Методы для распределения каналов
    def distribute_channels(self, channels: list) -> Optional[Dict]:
        """Распределяет каналы по аккаунтам"""
        return self._make_request("POST", "/auth/distribute_channels", {"channels": channels})
    
    def distribute_channels_from_db(self) -> Optional[Dict]:
        """Распределяет каналы из БД"""
        return self._make_request("POST", "/auth/distribute_channels_from_db")
    
    # Методы для парсинга
    def parse_all_sources(self, limit: int = None) -> Optional[Dict]:
        """Запускает парсинг всех источников"""
        data = {"limit": limit} if limit is not None else {}
        return self._make_request("POST", "/parsing/parse_all_sources", data)
    
    def parse_rss_sources(self, limit: int = None) -> Optional[Dict]:
        """Запускает парсинг только RSS источников"""
        data = {"limit": limit} if limit is not None else {}
        return self._make_request("POST", "/parsing/parse_rss_sources", data)
    
    def parse_telegram_sources(self, limit: int = None) -> Optional[Dict]:
        """Запускает парсинг только Telegram источников"""
        data = {"limit": limit} if limit is not None else {}
        return self._make_request("POST", "/parsing/parse_telegram_sources", data)
    
    def parse_specific_source(self, source_url: str, source_type: str = "auto") -> Optional[Dict]:
        """Запускает парсинг конкретного источника"""
        return self._make_request("POST", "/parsing/parse_specific_source", {
            "source_url": source_url,
            "source_type": source_type
        })
    
    def get_parsing_status(self) -> Optional[Dict]:
        """Получает статус парсинга и статистику"""
        return self._make_request("GET", "/parsing/status")
    
    # Методы для отладки
    def debug_sessions(self) -> Optional[Dict]:
        """Получает отладочную информацию о сессиях"""
        return self._make_request("GET", "/auth/debug_sessions")

# Глобальный экземпляр клиента
auth_service_client = AuthServiceClient() 