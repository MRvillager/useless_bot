from __future__ import annotations

from enum import Enum, auto
from typing import Iterable, Type, Union

from discord import Member, User


class Status(Enum):
    Win = auto()
    Lost = auto()
    Bust = auto()
    Push = auto()
    Stand = auto()
    Continue = auto()


class Player:
    def __init__(self, name: str, bet: int = 0):
        self._cards: list[int] = []
        self.name = name
        self.bet = bet
        self._status = Status.Continue

    def append(self, val: int):
        """Append a new card to player's hand"""
        self._cards.append(val)

    @property
    def hand_value(self) -> int:
        """Calculate player's hand value and return it"""
        card_sum = 0
        aces = 0

        for card in self._cards:
            if card == 14:
                aces += 1
            elif 11 <= card <= 13:
                card_sum += 10
            else:
                card_sum += card

        if aces > 0:
            if card_sum < (12 - aces):
                card_sum += 11 + (aces - 1)  # 11 + 10 = 21
            else:
                card_sum += aces

        return card_sum

    @property
    def hand(self) -> Iterable[str]:
        """Parse the player's hand and return an iterator"""
        for card in self._cards:
            if card == 11:
                yield "J"
            elif card == 12:
                yield "Q"
            elif card == 13:
                yield "K"
            elif card == 14:
                yield "A"
            else:
                yield str(card)

    @property
    def status(self) -> Status:
        """Calculate the player's status using his points"""
        points = self.hand_value
        if self._status != Status.Continue:
            pass
        elif points > 21:
            self._status = Status.Bust
        elif points < 21:
            self._status = Status.Continue
        elif points == 21:
            self._status = Status.Stand

        return self._status

    @status.setter
    def status(self, value: Status):
        """Override player status"""
        self._status = value

    @classmethod
    def from_discord(cls: Type[Player], member: Union[User, Member]) -> Player:
        """Create a player object using a discord.py member object"""
        return cls(name=member.name)


class Dealer(Player):
    def __init__(self):
        super().__init__("Dealer")

    @property
    def status(self) -> Status:
        """Calculate the dealer's status using his points"""
        points = self.hand_value

        if self._status != Status.Continue:
            pass
        elif points > 21:
            self._status = Status.Bust
        elif points < 17:
            self._status = Status.Continue
        elif 17 <= points <= 21:
            self._status = Status.Stand

        return self._status
