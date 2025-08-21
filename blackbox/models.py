from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId

class TelegramChannel(BaseModel):
    """Модель Telegram канала"""
    id: int = Field(..., description="ID канала")
    title: str = Field(..., description="Название канала")
    username: Optional[str] = Field(None, description="Username канала")
    type: str = Field(default="channel", description="Тип чата")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Дата создания записи")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Дата обновления записи")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class DigestSchedule(BaseModel):
    """Модель расписания дайджеста"""
    id: str = Field(..., description="Уникальный ID дайджеста")
    category: str = Field(..., description="Категория для дайджеста")
    time: str = Field(..., description="Время отправки в формате HH:MM")
    is_active: bool = Field(default=True, description="Активен ли дайджест")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Дата создания")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Дата обновления")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class TelegramChannelWithDigests(BaseModel):
    """Модель Telegram канала с дайджестами"""
    channel: TelegramChannel
    digests: List[DigestSchedule] = Field(default_factory=list, description="Список дайджестов")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class DigestTemplate(BaseModel):
    """Шаблон для дайджеста"""
    category: str
    title: str
    description: str
    time: str
    is_active: bool = True 