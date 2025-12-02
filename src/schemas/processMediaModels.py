from pydantic import BaseModel, HttpUrl, field_validator, Field
from typing import List, Dict


class TextToSpeechBlock(BaseModel):
    text: str
    voice: str


class ProcessMediaRequest(BaseModel):
    task_name: str
    video_blocks: Dict[str, List[HttpUrl]]
    audio_blocks: Dict[str, List[HttpUrl]]
    text_to_speech: List[TextToSpeechBlock]

    @classmethod
    @field_validator('video_blocks', 'audio_blocks')
    def validate_blocks_not_empty(cls, value):
        if not value:
            raise ValueError('Block dictionaries cannot be empty')
        for block_name, urls in value.items():
            if not urls:
                raise ValueError(f'Block {block_name} cannot be empty')
        return value


class TaskResponse(BaseModel):
    task_name: str
    status: str
    task_id: str
