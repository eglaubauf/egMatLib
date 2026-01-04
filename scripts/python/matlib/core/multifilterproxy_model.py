"""
Provides a Model for filtering multiple Parameters at the same time
"""

from PySide6 import QtCore


class MultiFilterProxyModel(QtCore.QSortFilterProxyModel):
    """
    Provides a Model for filtering multiple Parameters at the same time
    """

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__()
        self._filters = {}

    def setFilter(self, filter_role, filter_value):
        """
        Sets the Filter for the given role

        :param self: Description
        :param filter_role: Description
        :param filter_value: Description
        """
        self._filters[filter_role] = filter_value
        self.invalidateFilter()

    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> bool:
        if not self._filters:
            return True

        for role, curr_filter in self._filters.items():
            index = self.sourceModel().index(source_row, 0, source_parent)
            data = index.data(role)
            if isinstance(data, (list, tuple)):
                for elem in data:
                    if curr_filter.lower() != str(elem).lower():
                        return False
            elif isinstance(data, bool):
                if curr_filter != data and curr_filter != "":
                    return False
            elif curr_filter.lower() != data.lower():
                return False
        return True
