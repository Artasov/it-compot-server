from celery import shared_task

from apps.transcribe.services.common import send_transcribe_lead_call_report


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 320})
def transcribe_lead_call_report_task(lead_id: int, contact_id: int, transcript: str, ):
    send_transcribe_lead_call_report(
        lead_id=lead_id,
        contact_id=contact_id,
        text=transcript
    )
