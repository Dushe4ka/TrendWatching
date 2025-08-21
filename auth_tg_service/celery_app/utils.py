import asyncio
import time
import logging

log = logging.getLogger(__name__)

def run_async(coro_func):
    """
    Универсальная функция для запуска async кода в Celery задачах.
    Упрощенная версия для Linux с prefork pool.
    """
    try:
        # Пытаемся использовать существующий loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если loop уже запущен, создаем новый
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro_func())
            finally:
                loop.close()
        else:
            # Если loop не запущен, используем его
            return loop.run_until_complete(coro_func())
    except RuntimeError:
        # Если нет активного loop, создаем новый
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro_func())
        finally:
            loop.close()

def monitor_performance(func):
    """
    Декоратор для мониторинга производительности задач
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        task_name = func.__name__
        
        try:
            # Фильтруем аргументы, убирая служебные аргументы Celery
            filtered_args = args
            filtered_kwargs = kwargs.copy()
            
            # Убираем служебные аргументы Celery
            for key in ['request', 'task_id', 'task_name', 'task', 'args', 'kwargs']:
                filtered_kwargs.pop(key, None)
            
            result = func(*filtered_args, **filtered_kwargs)
            duration = time.time() - start_time
            
            if duration > 5.0:  # Предупреждение если задача выполняется больше 5 секунд
                log.warning(f"Task {task_name} took {duration:.2f}s - consider optimization")
            else:
                log.info(f"Task {task_name} completed in {duration:.3f}s")
                
            return result
        except Exception as e:
            duration = time.time() - start_time
            log.error(f"Task {task_name} failed after {duration:.3f}s: {e}")
            raise
    
    # Сохраняем оригинальное имя функции для Celery
    wrapper.__name__ = func.__name__
    wrapper.__module__ = func.__module__
    return wrapper