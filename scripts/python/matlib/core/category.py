"""
Stores the Category Model for the MatLib Panel and provides the data to it's corresponding view
Uses QtCore.QAbstractListModel as a Base Class
"""

from typing import Any
from PySide6 import QtCore

from matlib.prefs import prefs
from matlib.core import database


class Categories(QtCore.QAbstractListModel):
    """
    Stores the Category Model for the MatLib Panel and provides the data to it's corresponding view
    Uses QtCore.QAbstractListModel as a Base Class
    """

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__()

        preferences = prefs.Prefs()
        preferences.load()
        db = database.DatabaseConnector()
        self._data = db.load(preferences.dir)
        self._categories = self._data["categories"]
        self.CatSortRole = QtCore.Qt.ItemDataRole.UserRole  # 256

    def rowCount(
        self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | None = None
    ) -> int:
        return len(self._categories)

    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int = 0
    ) -> Any:
        if role == self.CatSortRole:
            return self._categories[index.row()]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            elem = self._categories[index.row()]
            if elem.startswith("_"):
                elem = elem[1:]
            return elem

    def switch_model_data(self, preferences):
        db = database.DatabaseConnector()
        data = db.reload_with_path(preferences.dir)
        self._categories = data["categories"]

    def remove_category(self, cat: str) -> None:
        """Removes the given category from the library (and also in all assets)"""
        self._categories.remove(cat)
        self.save()

    def rename_category(self, old: str, new: str) -> None:
        """Renames the given category in the library (and also in all assets)"""
        # Update Categories with that name
        for count, current in enumerate(self._categories):
            if current == old:
                self._categories[count] = new
        self.save()

    def check_add_category(self, cat: str) -> None:
        """Checks if this category exists and adds it if needed"""
        for c in cat.split(","):
            c = c.replace(" ", "")
            if c != "" and c not in self._categories:
                self._categories.append(c)

        self.save()

    def save(self) -> None:
        """Save data to disk as json"""
        db = database.DatabaseConnector()
        data = {}
        data["categories"] = self._categories
        db.set(data)
        db.save()
