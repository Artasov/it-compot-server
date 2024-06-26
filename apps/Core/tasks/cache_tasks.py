from celery import shared_task
from django.conf import settings

from service.pickler import Pickler


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 10, 'countdown': 20})
def pickler_delete_expired_cache():
    Pickler(**settings.PICKLER_SETTINGS).delete_expired()
