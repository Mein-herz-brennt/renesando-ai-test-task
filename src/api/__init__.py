from fastapi import APIRouter
from src.api.processMedia import router as process_media_router

router = APIRouter()
router.include_router(process_media_router)
