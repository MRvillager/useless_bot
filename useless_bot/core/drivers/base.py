from abc import ABC, abstractmethod
from typing import Any, Union, TypeVar

KeysSet = TypeVar('KeysSet', tuple[Union[str, int], ...], list[Union[str, int], ...])


class Base(ABC):
    _data: Any

    @abstractmethod
    async def setdefault(self, cog: str, keys: KeysSet, value: Any = None) -> None:
        """Initialize a sub_key if not already initialized"""
        ...

    @abstractmethod
    async def set(self, cog: str, keys: KeysSet, value: Any) -> None:
        """Set a value to a sub_key"""
        ...

    @abstractmethod
    async def get(self, cog: str, keys: KeysSet) -> Any:
        """Get the value knowing his location"""
        ...

    @abstractmethod
    async def delete(self, cog: str, keys: KeysSet) -> None:
        """Delete a sub_key and its value"""
        ...

    @abstractmethod
    def register(self, cog: str, *, schema: dict, override_schema: bool) -> None:
        """Initialize a main_key in data if not already initialized"""
        ...

    @abstractmethod
    async def unregister(self, cog: str) -> None:
        """Delete main_key and its sub_keys from data"""
        ...

    @abstractmethod
    async def dump(self) -> None:
        """Save data"""
        ...

    async def _load(self) -> None:
        """Load data"""
        raise NotImplementedError
