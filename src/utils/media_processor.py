import os
import random
import time
import itertools
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from google.cloud import storage
from src.settings import settings
import logging

logger = logging.getLogger(__name__)

TEMP_DIR = "/app/temp_media"


def download_file(url: str, dest_folder: str) -> str:
    """Завантажує файл за URL і повертає локальний шлях."""
    os.makedirs(dest_folder, exist_ok=True)
    filename = url.split("/")[-1]
    filepath = os.path.join(dest_folder, filename)

    # Оптимізація: не качати, якщо вже є
    if os.path.exists(filepath):
        return filepath

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
    return filepath


def generate_elevenlabs_speech(text: str, voice_id: str, dest_folder: str) -> str:
    """Генерує озвучку через ElevenLabs API."""
    # Примітка: voice_id має бути реальним ID від ElevenLabs, або мапитись з імені "Sarah"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {"text": text}

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        os.makedirs(dest_folder, exist_ok=True)
        filepath = os.path.join(dest_folder, f"tts_{hash(text)}.mp3")
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return filepath
    return None


def upload_to_gcs(local_path: str, destination_blob_name: str):
    """Завантажує готове відео в GCS."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_path)
        logger.info(f"Uploaded {local_path} to {destination_blob_name}")
    except Exception as e:
        logger.error(f"GCS Upload failed: {e}")


def process_task_logic(data: dict):
    start_time = time.time()
    task_name = data['task_name']
    video_blocks = data['video_blocks']

    # 1. Підготовка комбінацій (Cartesian product)
    # Сортуємо ключі, щоб порядок блоків був правильний (block1, block2...)
    sorted_block_keys = sorted(video_blocks.keys())
    list_of_video_lists = [video_blocks[key] for key in sorted_block_keys]

    # Генерує всі варіанти (наприклад 3x3x3 = 27)
    combinations = list(itertools.product(*list_of_video_lists))

    logger.info(f"Task {task_name}: Found {len(combinations)} combinations.")

    processed_count = 0

    for idx, combo_urls in enumerate(combinations):
        try:
            # 2. Завантаження ресурсів для поточної комбінації
            video_clips = []
            for url in combo_urls:
                local_path = download_file(url, os.path.join(TEMP_DIR, "videos"))
                video_clips.append(VideoFileClip(local_path))

            # 3. Склеювання відео (concatenation)
            final_clip = concatenate_videoclips(video_clips, method="compose")

            # 4. Випадкове аудіо (Background)
            all_bg_audio_urls = [url for sublist in data['audio_blocks'].values() for url in sublist]
            bg_music_url = random.choice(all_bg_audio_urls)
            bg_music_path = download_file(bg_music_url, os.path.join(TEMP_DIR, "audio"))

            bg_music = AudioFileClip(bg_music_path)
            # Зациклити, якщо відео довше, і обрізати, якщо коротше
            if bg_music.duration < final_clip.duration:
                bg_music = bg_music.fx(lambda c: c.loop(duration=final_clip.duration))
            else:
                bg_music = bg_music.subclip(0, final_clip.duration)

            bg_music = bg_music.volumex(0.2)  # Приглушити до 0.2

            # 5. Випадкова озвучка (TTS)
            tts_config = random.choice(data['text_to_speech'])
            # Тут треба мапінг імен на ID ElevenLabs, для прикладу беремо config.voice як ID
            tts_path = generate_elevenlabs_speech(tts_config['text'], "ELEVENLABS_VOICE_ID_HERE",
                                                  os.path.join(TEMP_DIR, "tts"))

            audio_layers = [bg_music]
            if tts_path:
                voice_clip = AudioFileClip(tts_path)
                # Можна додати voice_clip.set_start(1) щоб почати не одразу
                audio_layers.append(voice_clip)

            # 6. Міксування аудіо та накладання на відео
            final_audio = CompositeAudioClip(audio_layers)
            final_clip.audio = final_audio

            # 7. Експорт
            output_filename = f"{task_name}_combo_{idx}.mp4"
            output_path = os.path.join(TEMP_DIR, output_filename)

            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24, logger=None)

            # 8. Завантаження в хмару
            upload_to_gcs(output_path, f"{task_name}/{output_filename}")

            # Очистка пам'яті кліпів
            final_clip.close()
            for clip in video_clips: clip.close()
            os.remove(output_path)  # Видалити локальний результат

            processed_count += 1

        except Exception as e:
            logger.error(f"Error processing combo {idx}: {e}")

    total_time = time.time() - start_time
    logger.info(f"Task {task_name} finished. Processed {processed_count} videos in {total_time:.2f}s")