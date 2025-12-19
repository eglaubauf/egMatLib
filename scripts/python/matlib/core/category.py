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
        db = database.DatabaseConnector()
        _data = db.load(preferences.dir)
        self._categories = _data["categories"]

    def rowCount(
        self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | None = None
    ) -> int:
        return len(self._categories)

    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int = 0
    ) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._categories[index.row()]
