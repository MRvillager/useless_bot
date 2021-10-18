from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from typing import Union, Final, AsyncIterator

from nextcord import User, Member

from .config import Config
from .errors import BalanceOverLimitError, BalanceUnderLimitError

MAX_BALANCE: Final = pow(2, 32)

logger = logging.getLogger("useless_bot.core.bank_core")

schema = {
    "users": {}
}


@dataclass()
class BankUser:
    user_id: int
    balance: int = 50
    last_free_credits: int = 0


class BankCore:
    _config: Config

    def __init__(self):
        self.__class__._config = Config("BankCore", schema=schema)

    async def add_user(self, user: Union[User, Member, int]):
        """Add a user in the database"""
        if type(user) is int:
            user_id = user
        else:
            user_id = user.id

        await self._config.set(keys=("users", user_id), value=asdict(BankUser(user_id)))

    async def get_user(self, user: Union[User, Member, int]) -> BankUser:
        if type(user) is int:
            user_id = user
        else:
            user_id = user.id

        try:
            user_data = await self._config.get(keys=("users", user_id))
            user = BankUser(**user_data)
        except KeyError:
            user = BankUser(user_id)
            await self._config.set(keys=("users", user_id), value=asdict(user))
        finally:
            return user

    async def del_user(self, user: Union[User, Member, int]):
        if type(user) is int:
            user_id = user
        else:
            user_id = user.id

        await self._config.delete(keys=("users", user_id))

    async def balance(self, user: Union[User, Member]) -> int:
        return await self._config.get(keys=("users", user.id, "balance"))

    async def last_free_credits(self, user: Union[User, Member]) -> int:
        return await self._config.get(keys=("users", user.id, "last_free_credits"))

    async def update_last_free_credits(self, user: Union[User, Member], new_time: int):
        await self._config.set(keys=("users", user.id, "last_free_credits"), value=new_time)

    async def clear(self):
        """Reset database"""
        await self._config.delete_data()
        await self._config.init()

    async def _subtraction(self, user: Union[User, Member], value: int) -> int:
        new_value = await self.balance(user) - value
        if new_value >= 0:
            return new_value
        else:
            raise BalanceUnderLimitError

    async def _addition(self, user: Union[User, Member], value: int) -> int:
        new_value = await self.balance(user) + value
        if new_value < MAX_BALANCE:
            return new_value
        else:
            raise BalanceOverLimitError

    async def withdraw(self, user: Union[User, Member, int], value: int):
        if type(user) is int:
            user_id = user
        else:
            user_id = user.id

        logger.debug(f"Withdrawing {value} credits from {user_id}")
        value = await self._subtraction(user, value)
        await self._config.set(keys=("users", user_id, "balance"), value=value)
        logger.debug(f"Withdraw of {value} credits from {user_id}")

    async def deposit(self, user: Union[User, Member, int], value: int):
        if type(user) is int:
            user_id = user
        else:
            user_id = user.id

        logger.debug(f"Depositing {value} credits to {user_id}")
        value = await self._addition(user, value)
        await self._config.set(keys=("users", user_id, "balance"), value=value)
        logger.debug(f"Deposit of {value} credits to {user_id} complete")

    async def move(self, from_user: Union[User, Member], to_user: Union[User, Member], value: int):
        """Move credits from a user to another"""
        logger.debug(f"Moving {value} from <@{from_user}> to <@{to_user}>")

        await self.withdraw(user=from_user, value=value)
        await self.deposit(user=to_user, value=value)

    @property
    async def users(self) -> AsyncIterator[int]:
        # TODO: improve this, it's not efficient when there are a lot of users
        for user in await self._config.get(["users"]):
            yield user["id"]
