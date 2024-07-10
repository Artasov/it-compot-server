import logging

import requests
from django.conf import settings

log = logging.getLogger('base')


def send_transcribe_lead_call_report(lead_id: int, contact_id: int, text: str):
    response = requests.post(
        url=settings.AMOLINK_REPORT_CALL_TRANSCRIBTION,
        json={
            'lead_id': lead_id,
            'contact_id': contact_id,
            'text': text
        },
        headers={
            'Content-Type': 'application/json'
        }
    )
    if response.status_code == 200:
        log.info("Send transcribe lead call report was successful")
    else:
        log.error(f"Failed to send transcribe lead call report, status code: {response.status_code}")
