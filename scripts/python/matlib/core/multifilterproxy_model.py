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
        if not self._filters:
            return
        if filter_role in self._filters.keys():
            del self._filters[filter_role]

    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex,
    ) -> bool:
        if not self._filters:
            return True

        name_filter = True
        cat_filter = True
        fav_filter = True
        tag_filter = True
        render_filter = True
        for role, curr_filter in self._filters.items():
            index = self.sourceModel().index(source_row, 0, source_parent)
            data = index.data(role)

            if role == 0:  # Check Names
                if curr_filter == "":
                    name_filter = True
                if curr_filter.lower() not in data.lower():
                    name_filter = False
            elif role == 257:  # Check Category:
                if len(data) < 1:
                    cat_filter = False
                    if curr_filter == "":
                        cat_filter = True
                else:
                    for elem in data:
                        if curr_filter == "":
                            cat_filter = True
                        elif curr_filter.lower() != elem.lower():
                            cat_filter = False

            elif role == 258:  # Check Favorite:
                if curr_filter != data and curr_filter != "":
                    return False
            elif role == 259:  # Check Renderer:
                if curr_filter.lower() not in data.lower():
                    render_filter = False
            elif role == 260:  # is TagRole
                tag_filter = False
                for elem in data:
                    if curr_filter == "":
                        tag_filter = True
                    if curr_filter.lower() in str(elem).lower():
                        tag_filter = True

        if tag_filter and cat_filter and name_filter and fav_filter and render_filter:
            return True
        return False
