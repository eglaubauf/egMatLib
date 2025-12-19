"""
Database Handler for Matlib - Saves Data as json to disk and ensures only one active connection
"""

import json
from typing import Self


class DatabaseConnector:
    """
    Database Handler for Matlib - Saves Data as json to disk and ensures only one active connection
    """

    _instance = None
    _data = {}
    _path = ""

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        else:
            pass
        return cls._instance

    def load(self, path: str) -> dict:
        """
        Loads the Database from disk as json
        """
        self._path = path
        if not self._data:
            with open(self._path + ("/library.json"), encoding="utf_8") as lib_json:
                self._data = json.load(lib_json)
        return self._data

    def set(self, assets: dict) -> None:
        """Set Data without saving"""
        self._data = assets

    def save(self) -> None:
        """Save Data to Disk"""
        if not self._data:
            print("No Data")
            return
        with open(self._path + ("/library.json"), "w", encoding="utf-8") as lib_json:
            json.dump(self._data, lib_json, indent=4)
