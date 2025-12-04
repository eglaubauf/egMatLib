import os

from PySide6 import QtWidgets, QtCore, QtUiTools


# TODO: Remove references to library and make shure this is a view only


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
        self.cbx_render_on_import = self.ui.findChild(
            QtWidgets.QCheckBox, "cbx_renderOnImport"
        )

        self.buttons = self.ui.findChild(QtWidgets.QDialogButtonBox, "buttonBox")
        self.buttons.accepted.connect(self.confirm)
        self.buttons.rejected.connect(self.destroy)

        # Load Config from settings
        self.fill_values()

        # set main layout and attach to widget
        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addWidget(self.ui)
        mainlayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainlayout)

    # Apply Prefs Change
    def confirm(self):
        self.prefs.set_dir(self.line_workdir.text())
        self.prefs.save()

        self.library.rendersize = int(self.line_rendersize.text())
        self.library.thumbsize = int(self.line_thumbsize.text())
        self.library.render_on_import = int(self.cbx_render_on_import.isChecked())

        self.library.save()
        self.accept()

    # Cancel Prefs Change
    def destroy(self, destroyWindow=True, destroySubWindows=True) -> None:
        self.canceled = True
        self.close()

    # Fill UI
    def fill_values(self) -> None:
        self.directory = self.prefs.get_dir()
        self.rendersize = self.library.rendersize
        self.thumbsize = self.library.thumbsize
        self.render_on_import = self.library.render_on_import

        self.line_workdir.setText(self.directory)
        self.line_rendersize.setText(str(self.rendersize))
        self.line_thumbsize.setText(str(self.thumbsize))
        self.cbx_render_on_import.setChecked(self.render_on_import)
