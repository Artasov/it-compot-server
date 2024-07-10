import django
from celery import Celery
from celery.schedules import crontab

app = Celery('config')

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_connection_retry_on_startup = True
app.conf.update(
    task_always_eager=False,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    worker_concurrency=5,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=50,
    broker_transport_options={'max_retries': 3, 'interval_start': 0, 'interval_step': 0.5, 'interval_max': 2},
)
app.conf.CELERY_IMPORTS = (
    'apps.Core.tasks.test_tasks',
    'apps.Core.tasks.cache_tasks',
    'apps.tools.tasks.tasks',

)
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'clean_cache': {
        'task': 'apps.Core.tasks.cache_tasks.pickler_delete_expired_cache',
        'schedule': crontab(hour='0', minute='0'),
    },
    'upload_lasts_themes_task-every-day-10pm': {
        'task': 'apps.tools.tasks.tasks.upload_lasts_themes_task',
        'schedule': crontab(hour='22', minute='0'),
    },
}
# # Задача выполняется каждые 30 минут
# 'task-every-30-minutes': {
#     'task': 'Core.tasks.shared.common_tasks.test_periodic_task',
#     'schedule': crontab(minute='*/30'),
# },
# # Задача выполняется каждый час
# 'task-every-hour': {
#     'task': 'Core.tasks.shared.common_tasks.test_periodic_task',
#     'schedule': crontab(minute='0'),
# },
# # Задача выполняется каждые 2 часа
# 'task-every-2-hours': {
#     'task': 'Core.tasks.shared.common_tasks.test_periodic_task',
#     'schedule': crontab(minute='0', hour='*/2'),
# },
# Задача выполняется каждые 15 секунд
# 'task-every-15-seconds': {
#     'task': 'Core.tasks.test_periodic_task',
#     'schedule': timedelta(seconds=15),
#     'args': ('value1', 'value2'),  # Позиционные аргументы
#     # 'kwargs': {'param1': 'value1', 'param2': 'value2'},  # Или именованные аргументы
# },
# # Задача выполняется каждую секунду
# 'task-every-second': {
#     'task': 'Core.tasks.shared.common_tasks.test_periodic_task',
#     'schedule': timedelta(seconds=1),
# },
# # Задача выполняется каждую минуту
# 'task-every-minute': {
#     'task': 'Core.tasks.shared.common_tasks.test_periodic_task',
#     'schedule': crontab(minute='*'),
# },
# # Задача выполняется каждые 5 минут
# 'task-every-5-minutes': {
#     'task': 'Core.tasks.shared.common_tasks.test_periodic_task',
#     'schedule': crontab(minute='*/5'),
# },
# # Задача выполняется каждые 10 минут
# 'task-every-10-minutes': {
#     'task': 'Core.tasks.shared.common_tasks.test_periodic_task',
#     'schedule': crontab(minute='*/10'),
# },
