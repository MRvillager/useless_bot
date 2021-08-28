from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from sqlite3 import PrepareProtocol
from string import ascii_uppercase, digits
from typing import Optional, Union

# TODO: de-hardcode this
TOKEN_CHARSET = list(ascii_uppercase + digits)
TOKEN_LENGTH = 5


@dataclass(frozen=True)
class Transaction:
    id: int
    user: Union[User, int] = field(compare=False)
    amount: int = field(compare=False)
    refundable: bool = field(compare=False)
    reason: Optional[str] = field(compare=False)
    date: Union[datetime, str] = field(compare=False)

    @property
    def token(self):
        return self.id.to_bytes(TOKEN_LENGTH, byteorder='little', signed=False).decode("ascii")

    @classmethod
    def from_db(cls, data: tuple[int, Union[User, int], int, bool, Optional[str], Union[datetime, str]]) -> Transaction:
        return Transaction(*data)


@dataclass(frozen=True)
class User:
    user_id: int
    balance: int = field(compare=False)
    last_free_credits: int = field(repr=False, compare=False)

    def __str__(self):
        return str(self.user_id)

    def __conform__(self, protocol):
        if protocol is PrepareProtocol:
            return str(self.user_id)

    @classmethod
    def from_db(cls, data: tuple[int, int, int]) -> User:
        return User(*data)
