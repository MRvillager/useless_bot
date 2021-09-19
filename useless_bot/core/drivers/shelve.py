import pickle
import shelve
from typing import Any

from aiorwlock import RWLock

from .base import Base, KeysSet


class Shelve(Base):
    _data: shelve.Shelf = None
    _file: str

    _lock = RWLock()

    def __init__(self, *, file: str = "data/config"):
        self._file = file

        # Initialize _data
        if not self._data:
            self.__class__._data = shelve.open(self._file, flag='c', protocol=pickle.HIGHEST_PROTOCOL, writeback=True)

    async def setdefault(self, cog: str, keys: KeysSet, value: Any = None):
        # If main_key is not set, initialize it with an empty dict, otherwise do nothing
        partial = self.__class__._data[cog]
        for key in keys[:-1]:
            partial = partial[key]

        partial[keys[-1]].setdefault(cog, value)

    async def set(self, cog: str, keys: KeysSet, value: Any):
        partial = self.__class__._data[cog]

        for key in keys[:-1]:
            partial = partial[key]

        # noinspection PyUnusedLocal
        partial[keys[-1]] = value

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
        async with self._lock.writer_lock:
            # write updated data to file
            self._data.sync()

    async def _load(self):
        self.__class__._data = shelve.open(self._file, flag='c', protocol=pickle.HIGHEST_PROTOCOL, writeback=True)
