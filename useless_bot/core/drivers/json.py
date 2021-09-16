import logging

try:
    import orjson
    import aiofiles
except ImportError:
    logging.debug("Cannot import orjson and aiofiles. JSON driver not supported")

from typing import Any
from aiorwlock import RWLock

from .base import Base, KeysSet


class Json(Base):
    _data: dict = None
    _file: str
    _auto_save: bool

    _lock = RWLock()

    def __init__(self, *, auto_save: bool = True, file: str = "data/config.json"):
        self.__class__.file = file
        self.__class__._auto_save = auto_save

        # load data
        if not self._data:
            with open(self._file, "rb") as file:
                raw_data = file.read()

            # decode data
            self.__class__._data = orjson.loads(raw_data)

    async def setdefault(self, cog: str, keys: KeysSet, value: Any = None):
        # If main_key is not set, initialize it with an empty dict, otherwise do nothing
        partial = self.__class__._data[cog]
        for key in keys[:-1]:
            partial = partial[key]

        partial[keys[-1]].setdefault(cog, value)

    async def set(self, cog: str, keys: KeysSet, value: Any):
        partial = self.__class__._data[cog]

        for key in keys:
            partial = partial[key]

        partial = value

    async def get(self, cog: str, keys: KeysSet) -> Any:
        partial = self.__class__._data[cog]

        for key in keys[:-1]:
            partial = partial[key]

        return partial[keys[-1]]

    async def delete(self, cog: str, keys: KeysSet):
        partial = self.__class__._data[cog]

        for key in keys[:-1]:
            partial = partial[key]

        del partial[keys[-1]]

    def register(self, cog: str, *, schema: dict, override_schema: bool):
        if override_schema:
            self.__class__._data[cog] = schema
        else:
            self.__class__._data.setdefault(cog, schema)

    async def unregister(self, cog: str):
        # delete main key and its data
        del self.__class__._data[cog]

    async def dump(self):
        """Encode and save JSON data to file"""
        async with self._lock.writer_lock:
            # encode data
            raw_data = orjson.dumps(self._data)

            # save data to file
            async with open(self._file, "wb") as file:
                await file.write(raw_data)

    @classmethod
    async def _load(cls):
        """Read and decode JSON data from file"""
        async with cls._lock.writer_lock:
            # read data from file
            async with open(cls._file, "rb") as file:
                raw_data = await file.read()

            # decode data
            cls._data = orjson.loads(raw_data)
