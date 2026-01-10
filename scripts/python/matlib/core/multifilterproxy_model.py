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

    def removeFilter(self, filter_role):
        if filter_role in self._filters.keys():
            del self._filters[filter_role]

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
                    if role == 260:  # is TagRole
                        if curr_filter.lower() in str(elem).lower():
                            return True
                    if role == 257:  # is CatRole:
                        if curr_filter == "":
                            continue
                    if curr_filter.lower() != str(elem).lower():
                        return False
            elif isinstance(data, bool):
                if curr_filter != data and curr_filter != "":
                    return False
            elif curr_filter.lower() not in data.lower():
                return False
        return True
