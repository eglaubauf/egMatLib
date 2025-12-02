import os

from PySide6 import QtWidgets, QtCore, QtUiTools


class UsdDialog(QtWidgets.QDialog):
    def __init__(self) -> None:
        super(UsdDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        self.categories = ""
        self.tags = ""
        self.fav = False
        self.canceled = False

        # Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QtCore.QFile(self.script_path + "/ui/material_dialog.ui")
        file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # set main layout and attach to widget
        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addWidget(self.ui)
        mainlayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainlayout)

        # Link Slots & Signals
        self.line_cats = self.ui.findChild(QtWidgets.QLineEdit, "line_categories")
        self.line_tags = self.ui.findChild(QtWidgets.QLineEdit, "line_tags")
        self.cb_fav = self.ui.findChild(QtWidgets.QCheckBox, "cb_fav")

        self.buttons = self.ui.findChild(QtWidgets.QDialogButtonBox, "buttonBox")
        self.buttons.accepted.connect(self.confirm)
        self.buttons.rejected.connect(self.destroy)

    # Confirm material Creation
    def confirm(self) -> None:
        self.categories = self.line_cats.text()
        self.tags = self.line_tags.text()
        self.fav = self.cb_fav.isChecked()
        self.accept()

    # Cancel material Creation
    def destroy(self, destroyWindow=True, destroySubWindows=True) -> None:
        self.canceled = True
        self.close()
