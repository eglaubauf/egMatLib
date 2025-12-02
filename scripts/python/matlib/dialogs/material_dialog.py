import os

from PySide6 import QtWidgets, QtCore, QtUiTools


class MaterialDialog(QtWidgets.QDialog):
    def __init__(self):
        super(MaterialDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        # Set Vars
        self.categories = None
        self.tags = None
        self.fav = False
        self.canceled = False
        self.usd = False

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
        # FILTER UI
        self.line_cats = self.ui.findChild(QtWidgets.QLineEdit, "line_categories")
        self.line_tags = self.ui.findChild(QtWidgets.QLineEdit, "line_tags")
        self.cb_fav = self.ui.findChild(QtWidgets.QCheckBox, "cb_fav")
        self.cb_usd = self.ui.findChild(QtWidgets.CheckBox, "cb_usd")

        self.buttons = self.ui.findChild(QtWidgets.QDialogButtonBox, "buttonBox")
        self.buttons.accepted.connect(self.confirm)
        self.buttons.rejected.connect(self.destroy)

    # Confirm Material Creation
    def confirm(self):
        self.categories = self.line_cats.text()
        self.tags = self.line_tags.text()
        self.fav = self.cb_fav.isChecked()
        self.usd = self.cb_usd.isChecked()
        self.accept()

    # Cancel Material Creation
    def destroy(
        self, destroyWindow: bool = True, destroySubWindows: bool = True
    ) -> None:
        self.canceled = True
        self.close()
