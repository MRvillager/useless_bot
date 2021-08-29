import json
from typing import Any, Optional

CONFIG_FILE = "data/config.json"


class Config:
    data: Optional[dict[str, dict]] = None

    def __init__(self, name: str, auto_push: bool = True):
        self.auto_push = auto_push

        # change class name
        self.__name__ = name

        # load config file only one time
        if not self.data:
            self.pull()

        self.data.setdefault(self.__name__, {})

    def __getitem__(self, key: str) -> Any:
        try:
            return self.data[self.__name__][key]
        except KeyError:
            self.__setitem__(key, None)
            return None

    def __setitem__(self, key: str, value: Any):
        self.data[self.__name__][key] = value

        if self.auto_push:
            self.push()

    def setdefault(self, key: str, value: Any) -> Any:
        self.data[self.__name__].setdefault(key, value)

    @classmethod
    def pull(cls):
        try:
            with open(CONFIG_FILE, 'r') as outfile:
                cls.data = json.load(outfile)
        except FileNotFoundError:
            cls.data = {}
            Config.push()

    @classmethod
    def push(cls):
        with open(CONFIG_FILE, 'w') as outfile:
            json.dump(cls.data, outfile)
