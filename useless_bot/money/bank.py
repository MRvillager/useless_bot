from __future__ import annotations

import logging
import os.path
import sqlite3
from functools import wraps
from secrets import choice
from typing import Union, Callable, Optional, Iterable

from .errors import *
from .objects import TOKEN_CHARSET, TOKEN_LENGTH, User, Transaction

DB_FILE = "data/data.sqlite"

logger = logging.getLogger(__name__)


def check_user_id(function: Callable):
    """Sanitize user_id"""

    @wraps(function)
    def wrapper(self: Bank, user_id: int, *args, **kwargs):
        user_id = int(user_id)
        user_id_str = str(user_id)

        if len(user_id_str) not in [17, 18]:
            raise InvalidUserID
        if not user_id_str.isdigit():
            raise InvalidUserID

        value = function(self, user_id, *args, **kwargs)

        return value

    return wrapper


def check_user_existence(add: bool = False):
    """Add user to the database if is not already in"""

    def decor(function: Callable):
        @wraps(function)
        def wrapper(self: Bank, user_id: int, *args, **kwargs):
            if user_id not in self:
                if add:
                    self.unsafe_append(user_id)
                else:
                    raise UserIDNotRegistered

            value = function(self, user_id, *args, **kwargs)
            return value

        return wrapper

    return decor


class Bank:
    _db = None
    _user_id_cache: list = None

    def __init__(self):
        self.init_db()
        self._cur = self._db.cursor()

        if not self._user_id_cache:
            self.refresh_cache()

    def __len__(self) -> int:
        return len(self._user_id_cache)

    def init_db(self):
        if self._db is None:
            if not os.path.isfile(DB_FILE):
                with open("data/init.sql", "r") as f:
                    sql_as_string = f.read()
                create_db = True
            else:
                create_db = False

            self._db = sqlite3.connect(DB_FILE, isolation_level=None,
                                       detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

            if create_db:
                self._db.executescript(sql_as_string)

    @check_user_id
    @check_user_existence(add=True)
    def __getitem__(self, user_id: int) -> User:
        logger.debug(f"Retrieving <@{user_id}> from db")
        data = self._cur.execute("Select * From users Where user_id=:user_id Limit 1", {"user_id": user_id})
        return User.from_db(data.fetchone())

    @check_user_id
    def __delitem__(self, user_id: int):
        logger.debug(f"Deleting <@{user_id}> from db")
        self._user_id_cache.remove(user_id)
        self._cur.execute("Delete From users Where user_id=:user_id", {"user_id": user_id})

    @check_user_id
    def __contains__(self, user_id: int) -> bool:
        return user_id in self._user_id_cache

    def _token_exist(self, token: int) -> bool:
        response = self._cur.execute(
            "Select Case When Exists (Select 1 From transactions Where id=:id) "
            "Then Cast (1 AS BIT) Else Cast (0 AS BIT) End",
            {"id": token})
        return bool(response.fetchone()[0])

    def _gen_token(self) -> int:
        """Generate transaction id"""
        counter = 0
        while True:
            token = b""
            for _ in range(TOKEN_LENGTH):
                token += bytes(choice(TOKEN_CHARSET), "ascii")

            token_int = int.from_bytes(token, "little")

            if not self._token_exist(token_int):
                break
            else:
                counter += 1

            if counter > 100:
                logger.critical(f"Can't find an unused token after {counter} tries")
                raise TokenGenerationError()
        return token_int

    def unsafe_append(self, user_id: int):
        logger.debug(f"Adding <@{user_id}> to db")
        self._user_id_cache.append(user_id)
        self._cur.execute("Insert or Ignore Into users (user_id) values (:user_id)", {"user_id": user_id})

    def refresh_cache(self):
        """Refresh userid cache"""
        self._user_id_cache = list(self.users)
        logger.info(f"Loaded {len(self._user_id_cache)} into user_id cache")

    @check_user_id
    def append(self, user_id: int):
        """Add a user in the database"""
        self.unsafe_append(user_id)

    @check_user_id
    def remove(self, user_id: int):
        """Remove a user from the database"""
        logger.debug(f"Deleting <@{user_id}> from db")
        self._user_id_cache.remove(user_id)
        self._cur.execute("Delete From users Where user_id=:user_id", {"user_id": user_id})

    @check_user_id
    def pop(self, user_id: int) -> User:
        """
        Remove a user from the database and return it
        :param user_id: the id of the user
        :return: the removed user
        """
        logger.debug(f"Removing <@{user_id}> from db")
        self._user_id_cache.remove(user_id)
        data = self._cur.execute("Select * From users Where user_id=:user_id Limit 1", {"user_id": user_id})
        self._cur.execute("Delete From users Where user_id=:user_id", {"user_id": user_id})
        return User.from_db(data.fetchone())

    # noinspection SqlWithoutWhere
    def clear(self):
        """
        Reset database
        :return: None
        """
        logger.critical("Cleaning-up all db")
        self._user_id_cache = []
        self._cur.executescript("""
                                    DELETE FROM users;
                                    DELETE FROM transactions;
                                    VACUUM
                                """)

    @property
    def users(self) -> tuple:
        """:return a tuple containing all the user ids in the database """
        logger.info("retrieving all users in database")
        user_ids = self._cur.execute("Select user_id From users")
        return tuple(map(lambda x: x[0], user_ids))

    @check_user_id
    @check_user_existence()
    def get_transactions(self, user_id: int, limit: Optional[int] = 5) -> Iterable[Transaction]:
        if limit is None:
            logger.info(f"retrieving all transactions for <@{user_id}>")
            data = self._cur.execute("Select * From transactions Where user_id=:user_id", {"user_id": user_id})
        else:
            logger.debug(f"retrieving {limit} transactions for <@{user_id}>")
            data = self._cur.execute("Select * From transactions Where user_id=:user_id Limit 5", {"user_id": user_id})

        for row in data.fetchall():
            yield Transaction.from_db(row)

    @check_user_id
    @check_user_existence()
    def get_transaction(self, user_id: int, token: str) -> Transaction:
        logger.debug(f"retrieving transaction #{token} for <@{user_id}>")
        token_int = int.from_bytes(bytes(token, "ascii"), "little")
        data = self._cur.execute("Select * From transactions Where user_id=:user_id and id=:token Limit 1",
                                 {"user_id": user_id, "token": token_int})
        return Transaction.from_db(data.fetchone())

    @check_user_id
    @check_user_existence()
    def update_last_free_credits(self, user_id: int, new_time: int):
        logger.debug(f"updating last_free_credits for <@{user_id}>")
        self._cur.execute("UPDATE users SET last_free_credits=:time WHERE user_id=:user_id",
                          {"user_id": user_id, "time": new_time})

    def _balance(self, user_id: int) -> int:
        logger.debug(f"Retrieving balance from <@{user_id}>")
        return self._cur.execute("Select balance From users WHERE user_id=:user_id Limit 1",
                                 {"user_id": user_id}).fetchone()[0]

    def _check_sub(self, user_id: int, value: int) -> bool:
        return self._balance(user_id=user_id) + value < 0

    @check_user_id
    @check_user_existence()
    def transaction(self,
                    user_id: Union[User, int, str],
                    value: int,
                    refundable: bool = False,
                    reason: Optional[str] = None):
        """
        Remove or add money from a user, then log it in the database
        :param user_id: the interested party
        :param value: the value to add or subtract from the user's balance. Can be a negative or positive value
        :param refundable: set true for refundable transactions, for positive values it's always false
        :param reason: The reason for the transaction
        :return: None
        """
        if self._check_sub(user_id=user_id, value=value):
            raise BalanceNotSufficientError

        refundable = refundable and value < 0

        # process transaction
        if value > 0:
            refundable = False
            logger.debug(f"Adding {value} from <@{user_id}>")
            self._cur.execute("UPDATE users SET balance=balance+:value WHERE user_id=:user_id;",
                              {"user_id": user_id, "value": value})
        else:
            logger.debug(f"Removing {value} from <@{user_id}>")
            self._cur.execute("UPDATE users SET balance=balance-:value WHERE user_id=:user_id;",
                              {"user_id": user_id, "value": abs(value)})

        # log transaction to database
        token = self._gen_token()
        self._cur.execute("Insert Into transactions (id, user_id, amount, refundable, reason) values "
                          "(:id, :user_id, :amount, :refundable, :reason)",
                          {"id": token, "user_id": user_id, "amount": value, "refundable": refundable,
                           "reason": reason})

    # noinspection PyArgumentList
    def move(self, from_user: Union[User, int, str], to_user: Union[User, int], value: int):
        """
        Move money from a user to another
        :param from_user: user id
        :param to_user: the userid from which take the money
        :param value: the userid of the recipient
        :return: None
        """
        logger.debug(f"Moving {value} from <@{from_user}> to <@{to_user}>")
        reason = f"Move from <@{from_user}> to <@{to_user}>"

        self.transaction(user_id=from_user, value=-value, refundable=False, reason=reason)
        self.transaction(user_id=to_user, value=value, refundable=False, reason=reason)
