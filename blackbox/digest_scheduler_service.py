import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from telegram_channels_service import telegram_channels_service
from logger_config import setup_logger
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логгер
logger = setup_logger("digest_scheduler_service")

class DigestSchedulerService:
    """Сервис для планирования и отправки дайджестов в Telegram каналы"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.is_running = False
        self.scheduler_thread = None
    
    async def start_scheduler(self):
        """Запускает планировщик дайджестов"""
        if self.is_running:
            logger.info("Планировщик уже запущен")
            return
        
        self.is_running = True
        logger.info("Запуск планировщика дайджестов...")
        
        # Запускаем планировщик в отдельном потоке
        self.scheduler_thread = asyncio.create_task(self._scheduler_loop())
        
        logger.info("Планировщик дайджестов запущен")
    
    async def stop_scheduler(self):
        """Останавливает планировщик дайджестов"""
        if not self.is_running:
            logger.info("Планировщик уже остановлен")
            return
        
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.cancel()
            try:
                await self.scheduler_thread
            except asyncio.CancelledError:
                pass
        
        logger.info("Планировщик дайджестов остановлен")
    
    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        while self.is_running:
            try:
                # Получаем все активные дайджесты
                active_digests = telegram_channels_service.get_active_digests()
                
                # Планируем задачи для каждого дайджеста
                for digest in active_digests:
                    await self._schedule_digest(digest)
                
                # Ждем 1 минуту перед следующей проверкой
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Ошибка в цикле планировщика: {str(e)}")
                await asyncio.sleep(60)
    
    async def _schedule_digest(self, digest: Dict[str, Any]):
        """Планирует отправку дайджеста"""
        try:
            channel_id = digest["channel_id"]
            category = digest["category"]
            time_str = digest["time"]
            
            # Парсим время
            hour, minute = map(int, time_str.split(':'))
            
            # Создаем задачу для отправки дайджеста
            schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(
                self._send_digest_task, channel_id, category
            )
            
            logger.info(f"Запланирован дайджест для канала {channel_id}, категория {category}, время {time_str}")
            
        except Exception as e:
            logger.error(f"Ошибка при планировании дайджеста: {str(e)}")
    
    def _send_digest_task(self, channel_id: int, category: str):
        """Задача для отправки дайджеста (выполняется в отдельном потоке)"""
        try:
            # Создаем асинхронную задачу для отправки
            asyncio.create_task(self._send_digest(channel_id, category))
        except Exception as e:
            logger.error(f"Ошибка при создании задачи отправки дайджеста: {str(e)}")
    
    async def _send_digest(self, channel_id: int, category: str):
        """Отправляет дайджест в канал"""
        try:
            logger.info(f"Отправка дайджеста для канала {channel_id}, категория {category}")
            
            # Получаем данные для дайджеста
            digest_data = await self._generate_digest_data(category)
            
            if not digest_data:
                logger.warning(f"Нет данных для дайджеста категории {category}")
                return
            
            # Формируем текст дайджеста
            digest_text = self._format_digest_text(digest_data, category)
            
            # Отправляем дайджест в канал
            await self.bot.send_message(
                chat_id=channel_id,
                text=digest_text,
                parse_mode="Markdown"
            )
            
            logger.info(f"Дайджест успешно отправлен в канал {channel_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке дайджеста в канал {channel_id}: {str(e)}")
    
    async def _generate_digest_data(self, category: str) -> List[Dict[str, Any]]:
        """Генерирует данные для дайджеста по категории"""
        try:
            # Здесь должна быть логика получения данных из базы
            # Пока возвращаем заглушку
            return [
                {
                    "title": "Пример новости",
                    "description": "Описание новости",
                    "url": "https://example.com",
                    "date": datetime.now().strftime("%d.%m.%Y")
                }
            ]
        except Exception as e:
            logger.error(f"Ошибка при генерации данных дайджеста: {str(e)}")
            return []
    
    def _format_digest_text(self, data: List[Dict[str, Any]], category: str) -> str:
        """Форматирует текст дайджеста"""
        try:
            current_date = datetime.now().strftime("%d.%m.%Y")
            
            text = f"📰 **Дайджест новостей**\n\n"
            text += f"🏷️ Категория: {category}\n"
            text += f"📅 Дата: {current_date}\n"
            text += f"📊 Новостей: {len(data)}\n\n"
            
            if data:
                text += "**Последние новости:**\n\n"
                for i, item in enumerate(data[:5], 1):  # Показываем первые 5 новостей
                    text += f"{i}. **{item.get('title', 'Без заголовка')}**\n"
                    if item.get('description'):
                        text += f"   {item['description'][:100]}...\n"
                    if item.get('url'):
                        text += f"   🔗 [Читать далее]({item['url']})\n"
                    text += "\n"
                
                if len(data) > 5:
                    text += f"... и еще {len(data) - 5} новостей\n\n"
            else:
                text += "Новости не найдены.\n\n"
            
            text += "📱 Подпишитесь на бота для получения персональных дайджестов!"
            
            return text
            
        except Exception as e:
            logger.error(f"Ошибка при форматировании текста дайджеста: {str(e)}")
            return "❌ Ошибка при формировании дайджеста"
    
    async def run_scheduler(self):
        """Запускает планировщик в бесконечном цикле"""
        try:
            while self.is_running:
                schedule.run_pending()
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {str(e)}")
            self.is_running = False

# Глобальный экземпляр сервиса
digest_scheduler = None

def get_digest_scheduler(bot_instance=None):
    """Получает глобальный экземпляр планировщика дайджестов"""
    global digest_scheduler
    if digest_scheduler is None and bot_instance:
        digest_scheduler = DigestSchedulerService(bot_instance)
    return digest_scheduler 