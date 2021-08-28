import json
from typing import Any, Optional

data: Optional[dict[str, dict]] = None


class Config:
    def __init__(self, name: str, auto_push: bool = True):
        self.auto_push = auto_push

        # change class name
        self.__name__ = name

        # load config file only one time
        if not data:
            self.pull()

        data.setdefault(self.__name__, {})

    def __getitem__(self, key: str) -> Any:
        try:
            return data[self.__name__][key]
        except KeyError:
            self.__setitem__(key, None)
            return None

    def __setitem__(self, key: str, value: Any):
        data[self.__name__][key] = value

        if self.auto_push:
            self.push()

    def setdefault(self, key: str, value: Any) -> Any:
        data[self.__name__].setdefault(key, value)

    @staticmethod
    def pull():
        global data
        with open("data/config.json", 'r') as outfile:
            data = json.load(outfile)

    @staticmethod
    def push():
        with open("data/config.json", 'w') as outfile:
            json.dump(data, outfile)
