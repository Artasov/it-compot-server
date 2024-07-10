import os

from celery import shared_task

from transcribe.services.common import send_transcribe_lead_call_report
from modules.whisper.service import transcribe


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 320})
def transcribe_lead_call_task(lead_id: int, contact_id: int, temp_file_path: str, language: str):
    text = transcribe(temp_file_path, language)
    send_transcribe_lead_call_report(
        lead_id=lead_id,
        contact_id=contact_id,
        text=text
    )
    os.remove(temp_file_path)
