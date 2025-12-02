from fastapi import APIRouter, HTTPException
from src.schemas.processMediaModels import ProcessMediaRequest
from src.utils.tasks import process_media_task

router = APIRouter()


@router.post("/process_media", status_code=202)
async def process_media(request: ProcessMediaRequest):
    """
    Приймає JSON, валідує його та відправляє задачу в чергу Celery.
    Повертає ID задачі для відстеження.
    """
    try:
        # Конвертуємо Pydantic модель в dict для Celery
        task_payload = request.model_dump()

        # Відправка в чергу (async)
        task_result = process_media_task.delay(task_payload)

        return {
            "message": "Task submitted successfully",
            "task_id": task_result.id,
            "project_name": request.task_name,
            "status": 202
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))