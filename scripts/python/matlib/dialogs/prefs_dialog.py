import os

from PySide6 import QtWidgets, QtCore, QtUiTools


class PrefsDialog(QtWidgets.QDialog):
    def __init__(self, library, prefs) -> None:
        super(PrefsDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        self.library = library
        self.prefs = prefs
        self.canceled = False

        # Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QtCore.QFile(self.script_path + "/ui/prefs.ui")
        file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # UI
        self.line_workdir = self.ui.findChild(QtWidgets.QLineEdit, "line_workdir")
        self.line_thumbsize = self.ui.findChild(QtWidgets.QLineEdit, "line_thumbsize")
        self.line_rendersize = self.ui.findChild(QtWidgets.QLineEdit, "line_rendersize")
        self.cbx_renderOnImport = self.ui.findChild(
            QtWidgets.QCheckBox, "cbx_renderOnImport"
        )

        self.buttons = self.ui.findChild(QtWidgets.QDialogButtonBox, "buttonBox")
        self.buttons.accepted.connect(self.confirm)
        self.buttons.rejected.connect(self.destroy)

        # Load Config from settings
        self.fill_values()

        # set main layout and attach to widget
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.ui)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainLayout)

    # Apply Prefs Change
    def confirm(self):
        self.prefs.set_dir(self.line_workdir.text())
        self.prefs.save()

        self.library.set_renderSize(int(self.line_rendersize.text()))
        self.library.set_thumbsize(int(self.line_thumbsize.text()))
        self.library.set_renderOnImport(int(self.cbx_renderOnImport.isChecked()))

        self.library.save()
        self.accept()

    # Cancel Prefs Change
    def destroy(self, destroyWindow=True, destroySubWindows=True) -> None:
        self.canceled = True
        self.close()

    # Fill UI
    def fill_values(self) -> None:
        self.directory = self.prefs.get_dir()
        self.rendersize = self.library.get_renderSize()
        self.thumbsize = self.library.get_thumbsize()
        self.renderOnImport = self.library.get_renderOnImport()

        self.line_workdir.setText(self.directory)
        self.line_rendersize.setText(str(self.rendersize))
        self.line_thumbsize.setText(str(self.thumbsize))
        self.cbx_renderOnImport.setChecked(self.renderOnImport)
