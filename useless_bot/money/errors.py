__all__ = [
    "BalanceNotSufficientError",
    "InvalidUserID",
    "UserIDNotRegistered",
    "TokenGenerationError"
]


class BalanceNotSufficientError(Exception):
    pass


class InvalidUserID(Exception):
    pass


class UserIDNotRegistered(Exception):
    pass


class TokenGenerationError(Exception):
    pass
