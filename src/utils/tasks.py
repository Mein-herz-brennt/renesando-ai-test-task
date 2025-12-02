from celery import Celery
from src.settings import settings
from src.utils.media_processor import process_task_logic
import logging

celery_app = Celery('media_tasks', broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

logger = logging.getLogger(__name__)


@celery_app.task(name="process_media_task", bind=True)
def process_media_task(_, request_data: dict):
    """
    Celery task wrapper.
    Приймає dict (dump Pydantic моделі).
    """
    logger.info(f"Starting processing for task: {request_data.get('task_name')}")
    try:
        process_task_logic(request_data)
        return {"status": "success", "task_name": request_data.get('task_name')}
    except Exception as e:
        logger.error(f"Task failed: {e}")
        # Retry logic could be added here
        return {"status": "failed", "error": str(e)}
