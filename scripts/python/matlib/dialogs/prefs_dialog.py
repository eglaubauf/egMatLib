import os

from PySide6 import QtWidgets, QtCore, QtUiTools
from PySide6.QtGui import QCloseEvent


class PrefsDialog(QtWidgets.QDialog):
    def __init__(self, prefs) -> None:
        super(PrefsDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        self._prefs = prefs

        # Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QtCore.QFile(self.script_path + "/ui/prefs.ui")
        file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # UI
        self.line_workdir = self.ui.findChild(QtWidgets.QLineEdit, "line_workdir")
        self.line_thumbsize = self.ui.findChild(QtWidgets.QSpinBox, "line_thumbsize")
        self.line_rendersize = self.ui.findChild(QtWidgets.QSpinBox, "line_rendersize")
        self.cbx_render_on_import = self.ui.findChild(
            QtWidgets.QCheckBox, "cbx_renderOnImport"
        )
        self._cbx_matx = self.ui.findChild(QtWidgets.QCheckBox, "cbx_matx")
        self._cbx_matx.toggled.connect(self.toggle_matx)
        self._cbx_mantra = self.ui.findChild(QtWidgets.QCheckBox, "cbx_mantra")
        self._cbx_mantra.toggled.connect(self.toggle_mantra)
        self._cbx_arnold = self.ui.findChild(QtWidgets.QCheckBox, "cbx_arnold")
        self._cbx_arnold.toggled.connect(self.toggle_arnold)
        self._cbx_redshift = self.ui.findChild(QtWidgets.QCheckBox, "cbx_redshift")
        self._cbx_redshift.toggled.connect(self.toggle_redshift)
        self._cbx_octane = self.ui.findChild(QtWidgets.QCheckBox, "cbx_octane")
        self._cbx_octane.toggled.connect(self.toggle_octane)

        # Load Config from settings
        self.fill_values()

        # set main layout and attach to widget
        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addWidget(self.ui)
        mainlayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainlayout)

    def toggle_matx(self):
        self._prefs.renderer_matx_enabled = (
            True if self._cbx_matx.isChecked() else False
        )

    def toggle_mantra(self):
        self._prefs.renderer_mantra_enabled = (
            True if self._cbx_mantra.isChecked() else False
        )

    def toggle_arnold(self):
        self._prefs.renderer_arnold_enabled = (
            True if self._cbx_arnold.isChecked() else False
        )

    def toggle_redshift(self):
        self._prefs.renderer_redshift_enabled = (
            True if self._cbx_redshift.isChecked() else False
        )

    def toggle_octane(self):
        self._prefs.renderer_octane_enabled = (
            True if self._cbx_octane.isChecked() else False
        )

    def set_rendersize(self):
        self._prefs.rendersize = self.line_rendersize.value()

    def set_thumbsize(self):
        self._prefs.thumbsize = self.line_thumbsize.value()

    def set_render_on_import(self):
        self._prefs.render_on_import = int(self.cbx_render_on_import.isChecked())

    def closeEvent(self, arg__1: QCloseEvent) -> None:
        self._prefs.save()

    # Fill UI
    def fill_values(self) -> None:
        self.directory = self._prefs.dir
        self.rendersize = self._prefs.rendersize
        self.thumbsize = self._prefs.thumbsize
        self.render_on_import = self._prefs.render_on_import

        self.line_workdir.setText(self.directory)
        self.line_rendersize.setValue(self.rendersize)
        self.line_thumbsize.setValue(self.thumbsize)
        self.cbx_render_on_import.setChecked(self.render_on_import)

        self._cbx_matx.setChecked(self._prefs.renderer_matx_enabled)
        self._cbx_mantra.setChecked(self._prefs.renderer_mantra_enabled)
        self._cbx_arnold.setChecked(self._prefs.renderer_arnold_enabled)
        self._cbx_redshift.setChecked(self._prefs.renderer_redshift_enabled)
        self._cbx_octane.setChecked(self._prefs.renderer_octane_enabled)
