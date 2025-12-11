from typing import Any
from PySide6 import QtCore

from matlib.prefs import prefs
from matlib.core import database


class Categories(QtCore.QAbstractListModel):
    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__()

        preferences = prefs.Prefs()
        db = database.DatabaseConnector()
        _data = db.load(preferences.dir)
        self._categories = _data["categories"]

    def rowCount(
        self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex = ...
    ) -> int:
        return len(self._categories)

    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int = 0
    ) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._categories[index.row()]
