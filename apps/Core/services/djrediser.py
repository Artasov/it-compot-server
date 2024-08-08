import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from django.core.cache import cache


class CacheByNameNotFound(Exception):
    pass


class CacheTimeoutExpired(Exception):
    pass


class DjRediser:
    def __init__(self, default_timeout=86400, auto_delete_expired=True):
        """
        Initializes the DjRediser instance.

        @param default_timeout: The default timeout for cache entries in seconds.
        @param auto_delete_expired: Whether to delete expired cache entries automatically.
        """
        self.cache = cache
        self.default_timeout = default_timeout
        self.auto_delete_expired = auto_delete_expired

    def _get_cache_key(self, name):
        """
        Constructs the cache key with the given name.

        @param name: The base name of the cache entry.
        @return: The full cache key.
        """
        return f'{name}'

    def _is_expired(self, timestamp, timeout):
        """
        Checks if the cache entry is expired.

        @param timestamp: The timestamp when the cache entry was created.
        @param timeout: The timeout for the cache entry in seconds.
        @return: True if the cache entry is expired, False otherwise.
        """
        expiration_time = datetime.fromtimestamp(timestamp) + timedelta(seconds=timeout)
        return datetime.now() >= expiration_time

    def cache(self, name, obj=None, timeout=None, raise_timeout=False, *args, **kwargs):
        """
        Caches the result of a function or returns the cached result if available.

        @param name: The base name of the cache entry.
        @param obj: The object or function to cache.
        @param timeout: Seconds before expiration.
        @param raise_timeout: Whether to raise an exception if the cache has expired.
        @return: The cached result or the result of the function call.
        """
        cache_key = self._get_cache_key(name)
        cached_data = self.cache.get(cache_key)

        if cached_data is not None:
            timestamp, timeout, result = cached_data
            if not self._is_expired(timestamp, timeout):
                return result
            elif raise_timeout:
                raise CacheTimeoutExpired(f'Timeout expired for {name}')
            elif self.auto_delete_expired:
                self.cache.delete(cache_key)

        if obj is None:
            raise CacheByNameNotFound(f'No cache found for {name}')
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

            timestamp = int(datetime.now().timestamp())
            timeout = timeout if timeout is not None else self.default_timeout
            self.cache.set(cache_key, (timestamp, timeout, result))
            return result

    async def acache(self, name, obj=None, timeout=None, raise_timeout=False, *args, **kwargs):
        """
        Asynchronously caches the result of a function or returns the cached result if available.

        @param name: The base name of the cache entry.
        @param obj: The object or function to cache.
        @param timeout: Seconds before expiration.
        @param raise_timeout: Whether to raise an exception if the cache has expired.
        @return: The cached result or the result of the function call.
        """
        cache_key = self._get_cache_key(name)
        cached_data = self.cache.get(cache_key)

        if cached_data is not None:
            timestamp, timeout, result = cached_data
            if not self._is_expired(timestamp, timeout):
                return result
            elif raise_timeout:
                raise CacheTimeoutExpired(f'Timeout expired for {name}')
            elif self.auto_delete_expired:
                self.cache.delete(cache_key)

        if obj is None:
            raise CacheByNameNotFound(f'No cache found for {name}')
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

            timestamp = int(datetime.now().timestamp())
            timeout = timeout if timeout is not None else self.default_timeout
            self.cache.set(cache_key, (timestamp, timeout, result))
            return result

    def delete(self, name):
        """
        Deletes the cache entry for the given name.

        @param name: The base name of the cache entry.
        """
        cache_key = self._get_cache_key(name)
        self.cache.delete(cache_key)

    def delete_all(self):
        """
        Deletes all cache entries.
        """
        self.cache.clear()
