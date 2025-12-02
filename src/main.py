from fastapi import FastAPI
from src.api import processMedia
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI(title="Video Generator Service")

# Підключення роутера
app.include_router(processMedia.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}