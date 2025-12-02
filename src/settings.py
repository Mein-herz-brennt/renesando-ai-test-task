from decouple import config


class Settings:
    CELERY_BROKER_URL = config('CELERY_BROKER_URL')
    ELEVENLABS_API_KEY = config("ELEVENLABS_API_KEY")
    GCS_BUCKET_NAME = config("GCS_BUCKET_NAME")
    GOOGLE_APPLICATION_CREDENTIALS = config("GOOGLE_APPLICATION_CREDENTIALS")


settings = Settings()
