from datetime import timedelta

from celery import Celery

app = Celery('config')

import os

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_connection_retry_on_startup = True

# Load task modules from all registered Django apps.
app.conf.beat_schedule = {
    # Задача выполняется каждые 15 секунд
    # 'some-task-every-15s': {
    #     'task': 'Core.tasks.test_periodic_task',
    #     'schedule': timedelta(seconds=15),
    #     'args': ('value1',),
    # },
}
app.conf.CELERY_IMPORTS = ('apps.Core.tasks',)
app.autodiscover_tasks()

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
