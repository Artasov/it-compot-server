import asyncio
import pickle
from concurrent.futures import ThreadPoolExecutor

from django.core.cache import cache


class PiedisCacheNotFound(Exception):
    pass


class Piedis:
    default_timeout = 24 * 60 * 60

    @staticmethod
    def cache(name, obj=None, timeout: int = default_timeout, *args, **kwargs):
        cached_data = cache.get(name)

        if obj is None:
            if cached_data is not None:
                return pickle.loads(cached_data)
            else:
                raise PiedisCacheNotFound(f'No cached data found for {name}')
        else:
            if cached_data is not None:
                return pickle.loads(cached_data)
            else:
                result = None
                if callable(obj):
                    if asyncio.iscoroutinefunction(obj):
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            result = loop.run_until_complete(obj(*args, **kwargs))
                        else:
                            result = asyncio.run(obj(*args, **kwargs))
                    else:
                        with ThreadPoolExecutor() as executor:
                            result = executor.submit(obj, *args, **kwargs).result()
                else:
                    result = obj

                cache.set(name, pickle.dumps(result), timeout=timeout)
                return result

    @staticmethod
    async def acache(name, obj=None, timeout: int = default_timeout, *args, **kwargs):
        cached_data = cache.get(name)

        if obj is None:
            if cached_data is not None:
                return pickle.loads(cached_data)
            else:
                raise PiedisCacheNotFound(f'No cached data found for {name}')
        else:
            if cached_data is not None:
                return pickle.loads(cached_data)
            else:
                result = None
                if callable(obj):
                    if asyncio.iscoroutinefunction(obj):
                        result = await obj(*args, **kwargs)
                    else:
                        with ThreadPoolExecutor() as executor:
                            loop = asyncio.get_event_loop()
                            result = await loop.run_in_executor(executor, obj, *args, **kwargs)
                else:
                    result = obj

                cache.set(name, pickle.dumps(result), timeout=timeout)
                return result

    @staticmethod
    def clean(name):
        cache.delete(name)
