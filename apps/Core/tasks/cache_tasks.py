import logging

from celery import shared_task
from django.conf import settings

from modules.pickler import Pickler

log = logging.getLogger('base')


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 10, 'countdown': 20})
def pickler_delete_expired_cache():
    log.warning('Deleting EXPIRED cache.')
    Pickler(**settings.PICKLER_SETTINGS).delete_expired()


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 10, 'countdown': 20})
def pickler_delete_all_cache():
    log.warning('Deleting ALL cache.')
    Pickler(**settings.PICKLER_SETTINGS).delete_all()
