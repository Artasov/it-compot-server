import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from django.conf import settings

from apps.tools.services.lesson_report.funcs import upload_lasts_themes_for_unit_student

log = logging.getLogger('base')


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 120})
def upload_lasts_themes_task():
    if 'code-academy' in settings.DOMAIN_URL:
        async_to_sync(upload_lasts_themes_for_unit_student)()
    else:
        print("DOMAIN NOT IS code-academy TASK NOT STARTED")
