import json
from typing import Self


class DatabaseConnector:
    _instance = None
    _data = {}
    _path = ""

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        else:
            print("Db Connection already exists")
        return cls._instance

    def load(self, path: str) -> dict:
        self._path = path
        if not self._data:
            with open(self._path + ("/library.json"), encoding="utf_8") as lib_json:
                self._data = json.load(lib_json)
        return self._data

    def save(self) -> None:
        if not self._data:
            return
        with open(self._path + ("/library.json"), "w", encoding="utf-8") as lib_json:
            json.dump(self._data, lib_json, indent=4)
