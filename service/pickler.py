import asyncio
import pickle
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class PicklerNotFoundDumpFile(Exception):
    pass


class Pickler:
    def __init__(self, base_temp_dir):
        self.base_temp_dir = Path(base_temp_dir)
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)

    def cache(self, name, obj=None, *args, **kwargs):
        dump_file_path = Path(self.base_temp_dir) / f'{name}.pkl'
        dump_file_path.parent.mkdir(parents=True, exist_ok=True)

        if obj is None:
            if dump_file_path.exists():
                with open(dump_file_path, 'rb') as f:
                    return pickle.load(f)
            else:
                raise PicklerNotFoundDumpFile(f'No dump file found for {name}')
        else:
            if dump_file_path.exists():
                with open(dump_file_path, 'rb') as f:
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

                with open(dump_file_path, 'wb') as f:
                    pickle.dump(result, f)
                return result

    async def acache(self, name, obj=None, *args, **kwargs):
        dump_file_path = Path(self.base_temp_dir) / f'{name}.pkl'
        dump_file_path.parent.mkdir(parents=True, exist_ok=True)

        if obj is None:
            if dump_file_path.exists():
                with open(dump_file_path, 'rb') as f:
                    return pickle.load(f)
            else:
                raise PicklerNotFoundDumpFile(f'No dump file found for {name}')
        else:
            if dump_file_path.exists():
                with open(dump_file_path, 'rb') as f:
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

                with open(dump_file_path, 'wb') as f:
                    pickle.dump(result, f)
                return result
