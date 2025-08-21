from pydantic import BaseModel, Field
from typing import List, Optional

class RequestCodeModel(BaseModel):
    phone_number: str = Field(..., example="+79991234567")
    api_id: int = Field(..., example=123456)
    api_hash: str = Field(..., example="your_api_hash")
    admin_chat_id: Optional[str] = None

class ConfirmCodeModel(BaseModel):
    phone_number: str
    code: str
    api_id: int
    api_hash: str
    admin_chat_id: Optional[str] = None

class SessionStatusRequest(BaseModel):
    phone_number: str

class RemoveSessionRequest(BaseModel):
    phone_number: str

class SessionInfo(BaseModel):
    session_id: str
    phone_number: str
    channels: List[str]
    created_at: str
    session_file_path: str

class ChannelBinding(BaseModel):
    session_id: str
    chat_id: str

class StatusResponse(BaseModel):
    total_accounts: int
    total_channels: int
    max_channels_per_account: int
    available_slots: int
    sessions: List[SessionInfo]
    not_loaded_channels: Optional[List[str]] = None 

class DistributeChannelsRequest(BaseModel):
    channels: list[str]

class DistributeChannelsResult(BaseModel):
    distributed: dict  # session_id -> list of channels
    not_loaded: list[str]
    total_slots: int
    sessions: Optional[List[SessionInfo]] = None 

class ConfirmPasswordModel(BaseModel):
    phone_number: str
    password: str
    api_id: int
    api_hash: str
    admin_chat_id: Optional[str] = None 

class ParseSourcesRequest(BaseModel):
    limit: int = 100
    chat_id: Optional[str] = None

class ParseRSSRequest(BaseModel):
    limit: int = 50
    chat_id: Optional[str] = None

class ParseTelegramRequest(BaseModel):
    limit: int = 50
    chat_id: Optional[str] = None

class ParseSpecificSourceRequest(BaseModel):
    source_url: str
    source_type: str = "auto"
    chat_id: Optional[str] = None

class ParsingResult(BaseModel):
    """Модель для результата парсинга"""
    task_id: str = Field(..., description="ID задачи")
    status: str = Field(..., description="Статус задачи")
    message: str = Field(default="", description="Дополнительное сообщение") 