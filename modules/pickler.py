import asyncio
import pickle
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path


class PicklerNotFoundDumpFile(Exception):
    """Exception raised when the dump file is not found."""
    pass


class PicklerTimeoutExpired(Exception):
    """Exception raised when the dump file timeout has expired."""
    pass


SECONDS_IN_DAY = 24 * 60 * 60


class Pickler:
    def __init__(self, base_temp_dir, separator='--', auto_delete_expired=True):
        """
        Initializes the Pickler instance.

        @param base_temp_dir: The base directory for storing cache files.
        @param separator: The separator for name, timestamp, and timeout in the filename.
        @param auto_delete_expired: Whether to delete expired cache files automatically.
        """
        self.base_temp_dir = Path(base_temp_dir)
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)
        self.separator = separator
        self.auto_delete_expired = auto_delete_expired

    def _get_dump_file_path(self, name, timestamp, timeout):
        """
        Constructs the dump file path with the given parameters.

        @param name: The base name of the cache file.
        @param timestamp: The timestamp when the cache file was created.
        @param timeout: The timeout for the cache file in seconds.
        @return: The full path to the cache file.
        """
        return Path(self.base_temp_dir) / f'{name}{self.separator}{timestamp}{self.separator}{timeout}.pkl'

    def _get_existing_dump_file(self, name):
        """
        Finds an existing dump file for the given name if it has not expired.

        @param name: The base name of the cache file.
        @return: The Path to the existing dump file or None if not found.
        """
        pattern = f'{name}{self.separator}*.pkl'
        for file in self.base_temp_dir.glob(pattern):
            parts = file.stem.split(self.separator)
            if len(parts) == 3:
                try:
                    timestamp = int(parts[1])
                    timeout = int(parts[2])
                    expiration_time = datetime.fromtimestamp(timestamp) + timedelta(seconds=timeout)
                    if datetime.now() < expiration_time:
                        return file
                    elif self.delete_expired:
                        file.unlink()
                except ValueError:
                    continue
        return None

    def cache(self, name, obj=None, timeout=SECONDS_IN_DAY, raise_timeout=False, *args, **kwargs):
        """
        Caches the result of a function or returns the cached result if available.

        @param name: The base name of the cache file.
        @param obj: The object or function to cache.
        @param timeout: Seconds before expiration.
        @param raise_timeout: Whether to raise an exception if the cache has expired.
        @return: The cached result or the result of the function call.
        """
        existing_file = self._get_existing_dump_file(name)

        if obj is None:
            if existing_file and existing_file.exists():
                with open(existing_file, 'rb') as f:
                    return pickle.load(f)
            else:
                if raise_timeout:
                    raise PicklerTimeoutExpired(f'Timeout expired for {name}')
                else:
                    raise PicklerNotFoundDumpFile(f'No dump file found for {name}')
        else:
            if existing_file and existing_file.exists():
                with open(existing_file, 'rb') as f:
                    return pickle.load(f)
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
                dump_file_path = self._get_dump_file_path(name, timestamp, timeout)
                with open(dump_file_path, 'wb') as f:
                    pickle.dump(result, f)
                return result

    async def acache(self, name, obj=None, timeout=SECONDS_IN_DAY, raise_timeout=False, *args, **kwargs):
        """
        Asynchronously caches the result of a function or returns the cached result if available.

        @param name: The base name of the cache file.
        @param obj: The object or function to cache.
        @param timeout: Seconds before expiration.
        @param raise_timeout: Whether to raise an exception if the cache has expired.
        @return: The cached result or the result of the function call.
        """
        existing_file = self._get_existing_dump_file(name)

        if obj is None:
            if existing_file and existing_file.exists():
                with open(existing_file, 'rb') as f:
                    return pickle.load(f)
            else:
                if raise_timeout:
                    raise PicklerTimeoutExpired(f'Timeout expired for {name}')
                else:
                    raise PicklerNotFoundDumpFile(f'No dump file found for {name}')
        else:
            if existing_file and existing_file.exists():
                with open(existing_file, 'rb') as f:
                    return pickle.load(f)
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
                dump_file_path = self._get_dump_file_path(name, timestamp, timeout)
                with open(dump_file_path, 'wb') as f:
                    pickle.dump(result, f)
                return result

    def delete_expired(self):
        """
        Deletes all expired cache files.
        """
        for file in self.base_temp_dir.glob(f'*{self.separator}*.pkl'):
            parts = file.stem.split(self.separator)
            if len(parts) == 3:
                try:
                    timestamp = int(parts[1])
                    timeout = int(parts[2])
                    if datetime.now() >= datetime.fromtimestamp(timestamp) + timedelta(seconds=timeout):
                        file.unlink()
                except ValueError:
                    continue

    def delete_all(self):
        """
        Deletes all cache files in the base temporary directory.
        """
        for file in self.base_temp_dir.glob('*.pkl'):
            file.unlink()

    def delete(self, name):
        """
        Deletes the cache file for the given name.

        @param name: The base name of the cache file.
        """
        pattern = f'{name}{self.separator}*.pkl'
        for file in self.base_temp_dir.glob(pattern):
            file.unlink()
