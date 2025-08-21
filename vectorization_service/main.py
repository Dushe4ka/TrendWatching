from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from vectorization_tasks import start_vectorization_task, get_vectorization_status
from database import (
    get_unvectorized_data_async, 
    update_vectorization_status_async,
    get_vectorized_data_count_async,
    get_unvectorized_data_count_async
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vectorization Service", version="1.0.0")

class VectorizationRequest(BaseModel):
    """Модель запроса на векторизацию"""
    chat_id: Optional[str] = None
    force: bool = False

class VectorizationStatus(BaseModel):
    """Модель статуса векторизации"""
    task_id: str
    status: str
    message: str
    vectorized_count: int = 0
    total_unvectorized: int = 0

@app.post("/vectorization/start", response_model=VectorizationStatus)
async def start_vectorization(request: VectorizationRequest):
    """Запускает процесс векторизации невекторизованных данных"""
    try:
        # Получаем количество невекторизованных записей
        unvectorized_count = await get_unvectorized_data_count_async()
        
        if unvectorized_count == 0 and not request.force:
            return VectorizationStatus(
                task_id="",
                status="no_data",
                message="Нет невекторизованных данных для обработки",
                vectorized_count=0,
                total_unvectorized=0
            )
        
        # Запускаем задачу векторизации
        task = start_vectorization_task.delay(
            chat_id=request.chat_id,
            force=request.force
        )
        
        return VectorizationStatus(
            task_id=task.id,
            status="started",
            message="Векторизация запущена",
            vectorized_count=0,
            total_unvectorized=unvectorized_count
        )
        
    except Exception as e:
        logger.error(f"Ошибка при запуске векторизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vectorization/status/{task_id}", response_model=VectorizationStatus)
async def get_vectorization_task_status(task_id: str):
    """Получает статус задачи векторизации"""
    try:
        status = get_vectorization_status(task_id)
        return VectorizationStatus(**status)
    except Exception as e:
        logger.error(f"Ошибка при получении статуса векторизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vectorization/stats")
async def get_vectorization_stats():
    """Получает статистику векторизации"""
    try:
        unvectorized_count = await get_unvectorized_data_count_async()
        vectorized_count = await get_vectorized_data_count_async()
        total_count = unvectorized_count + vectorized_count
        
        return {
            "total_records": total_count,
            "vectorized_records": vectorized_count,
            "unvectorized_records": unvectorized_count,
            "vectorization_percentage": (vectorized_count / total_count * 100) if total_count > 0 else 0
        }
    except Exception as e:
        logger.error(f"Ошибка при получении статистики векторизации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True) 