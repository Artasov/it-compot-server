import os
import shutil
import time

import torch
import whisper
from django.conf import settings

from transcribe.services.common import log


def transcribe(path: str, language: str = 'ru') -> str:
    if not os.path.isfile(path):
        raise Exception(f"File not found: {path}")
    if not shutil.which("ffmpeg"):
        raise Exception("ffmpeg not found in PATH")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    start_time = time.time()

    model = whisper.load_model(name='large-v2', download_root=settings.WHISPER_MODELS_DIR, device=device)
    result = model.transcribe(path, language=language)

    log.info(f'Transcription completed in {(time.time() - start_time):.2f} seconds for file: {path}')

    return result['text']
