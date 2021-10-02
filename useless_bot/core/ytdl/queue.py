from .models import BaseSong

__all__ = ["Queue"]


class Queue:
    repeat: bool = False
    loop: bool = False

    _stack: list[BaseSong] = []
    _index: int = 0

    def __iter__(self):
        return self._stack

    def __next__(self) -> BaseSong:
        if self.repeat:
            return self._stack[self._index]
        elif self.loop:
            value = self._stack[self._index]
            self._index += (self._index + 1) % len(self._stack)
            return value
        else:
            self._index = 0
            return self._stack.pop(0)

    def __getitem__(self, index: int) -> BaseSong:
        self._index = index % len(self)

        if self.loop or self.repeat:
            return self._stack[self._index]
        else:
            return self._stack.pop(self._index)

    def __setitem__(self, index: int, item: BaseSong) -> None:
        self._stack[index] = item

    def __delitem__(self, index: int) -> None:
        del self._stack[index]
        self._index = self._index % len(self)

    def __len__(self) -> int:
        return len(self._stack)

    def __contains__(self, item: BaseSong) -> bool:
        return item in self._stack

    def append(self, item: BaseSong) -> None:
        self._stack.append(item)

    def insert(self, index: int, item: BaseSong) -> None:
        self._stack.insert(index, item)
