import random
import string

from asgiref.sync import sync_to_async
from django.urls import reverse

from apps.link_shorter.models import Link


def generate_short_code():
    length = 6
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


async def create_short_link(url: str) -> str:
    while True:
        short_code = generate_short_code()
        link_exists = await sync_to_async(Link.objects.filter(short_code=short_code).exists)()
        if not link_exists:
            break
    # Используем sync_to_async для создания объекта в БД
    link = await Link.objects.acreate(original_url=url, short_code=short_code)
    # Использование reverse в асинхронной функции не вызывает проблем, так как это CPU-bound операция
    return reverse('redirect_to_full_link', kwargs={'short_code': link.short_code})
