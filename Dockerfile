FROM python:3.10-slim

# Встановлюємо системні залежності (FFmpeg потрібен для moviepy)
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Створюємо папку для тимчасових файлів
RUN mkdir -p /app/temp_media