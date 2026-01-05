"""
Material Import Dialog attached to the MatLibPanel
"""

import os

from PySide6 import QtWidgets, QtCore, QtUiTools


class UsdDialog(QtWidgets.QDialog):
    """
    Material Import Dialog attached to the MatLibPanel
    """

    def __init__(self, cat_list: list[str]) -> None:
        super(UsdDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        self.categories = ""
        self.tags = ""
        self.fav = False
        self.canceled = False

        loader = QtUiTools.QUiLoader()
        file = QtCore.QFile(self.script_path + "/ui/material_dialog.ui")
        file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addWidget(self.ui)
        mainlayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainlayout)

        self.combo_cats = self.ui.findChild(QtWidgets.QComboBox, "combo_categories")
        for cat in cat_list:
            self.combo_cats.addItem(cat)
        self.combo_cats.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.InsertAtTop)

        self.line_tags = self.ui.findChild(QtWidgets.QLineEdit, "line_tags")
        self.cb_fav = self.ui.findChild(QtWidgets.QCheckBox, "cb_fav")

        self.buttons = self.ui.findChild(QtWidgets.QDialogButtonBox, "buttonBox")
        self.buttons.accepted.connect(self.confirm)
        self.buttons.rejected.connect(self.destroy)

    def confirm(self) -> None:
        """
        Confirm material Creation

        :param self: Description
        """
        # self.categories = self.line_cats.text()
        self.categories = self.combo_cats.currentText()
        self.tags = self.line_tags.text()
        self.fav = self.cb_fav.isChecked()
        self.accept()

    def destroy(self, destroyWindow=True, destroySubWindows=True) -> None:
        """
        Cancel material Creation

        :param self: Description
        :param destroyWindow: Description
        :param destroySubWindows: Description
        """
        self.canceled = True
        self.close()
