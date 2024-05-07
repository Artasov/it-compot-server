from asgiref.sync import sync_to_async
from django.db.transaction import Atomic


class AsyncAtomicContextManager(Atomic):
    def __init__(self, using=None, savepoint=True, durable=False):
        super().__init__(using, savepoint, durable)

    async def __aenter__(self):
        await sync_to_async(super().__enter__)()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await sync_to_async(super().__exit__)(exc_type, exc_value, traceback)


def aatomic(fun, *args, **kwargs) -> callable:
    async def wrapper():
        async with AsyncAtomicContextManager():
            await fun(*args, **kwargs)

    return wrapper


async def arelated(model_object, related_field_name: str):
    return await sync_to_async(getattr)(model_object, related_field_name, None)


async def aall(queryset) -> list: 
    return await sync_to_async(list)(queryset.all())


async def afilter(queryset, *args, **kwargs) -> list:
    return await sync_to_async(list)(queryset.filter(*args, **kwargs))
