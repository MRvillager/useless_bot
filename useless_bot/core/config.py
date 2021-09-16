import logging

from contextlib import asynccontextmanager
from typing import Any
from aiorwlock import RWLock

from .drivers import Base, KeysSet

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, driver: Base, cog: str, schema=None, override_schema: bool = False):
        if schema is None:
            schema = {}

        self._driver = driver

        # set main key
        self._cog = cog

        # register main key
        self._driver.register(self._cog, schema=schema, override_schema=override_schema)

        # setup lock
        self._lock = RWLock()

        # transaction variables
        self._in_transaction = False

    async def get(self, keys: KeysSet) -> Any:
        with self._lock.reader_lock:
            logging.debug(f"Getting value for {self._cog}/{keys}")
            return await self._driver.get(cog=self._cog, keys=keys)

    async def set(self, keys: KeysSet, value: Any):
        with self._lock.writer_lock:
            logging.debug(f"Setting value for {self._cog}/{keys}")
            await self._driver.set(cog=self._cog, keys=keys, value=value)

            if not self._in_transaction:
                # save changes
                await self.save()

    async def delete(self, keys: KeysSet):
        with self._lock.writer_lock:
            logging.debug(f"Deleting value for {self._cog}/{keys}")
            await self._driver.delete(cog=self._cog, keys=keys)

            if not self._in_transaction:
                # save changes
                await self.save()

    async def setdefault(self, keys: KeysSet, value: Any) -> Any:
        with self._lock.writer_lock:
            await self._driver.setdefault(cog=self._cog, keys=keys, value=value)

            if not self._in_transaction:
                # save changes
                await self.save()

    async def delete_data(self):
        logging.info(f"Deleting all data for {self._cog}")
        await self._driver.unregister(cog=self._cog)

        if not self._in_transaction:
            # save changes
            await self.save()

    async def init(self, schema=None, override_schema: bool = False):
        if schema is None:
            schema = {}
        self._driver.register(self._cog, schema=schema, override_schema=override_schema)

    @asynccontextmanager
    async def transaction(self):
        logging.debug("Opening config transaction")
        self._in_transaction = True
        try:
            yield self
        finally:
            logging.debug("Saving changes")

            # save changes
            await self.save()

            self._in_transaction = False
            logging.debug("Closed config transaction")

    async def save(self):
        """Save changes"""
        logging.info("Saving data")
        await self._driver.dump()
        logging.info("Data Saved")
