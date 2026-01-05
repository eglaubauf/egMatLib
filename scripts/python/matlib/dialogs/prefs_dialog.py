"""
Preferences Dialog attached to the MatLibPanel
"""

import os

from PySide6 import QtWidgets, QtCore, QtUiTools
from PySide6.QtGui import QCloseEvent


class PrefsDialog(QtWidgets.QDialog):
    """
    Preferences Dialog attached to the MatLibPanel
    """

    def __init__(self, prefs) -> None:
        super(PrefsDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        self._prefs = prefs

        loader = QtUiTools.QUiLoader()
        file = QtCore.QFile(self.script_path + "/ui/prefs.ui")
        file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        self.line_workdir = self.ui.findChild(QtWidgets.QLineEdit, "line_workdir")
        self.line_thumbsize = self.ui.findChild(QtWidgets.QSpinBox, "line_thumbsize")
        self.line_rendersize = self.ui.findChild(QtWidgets.QSpinBox, "line_rendersize")
        self.line_rendersamples = self.ui.findChild(
            QtWidgets.QSpinBox, "line_rendersamples"
        )
        self._combo_ballmode = self.ui.findChild(
            QtWidgets.QComboBox, "combo_shaderball"
        )

        self._combo_ballmode.addItem("Simple")
        self._combo_ballmode.addItem("Complex (V1)")

        self._combo_ballmode.currentIndexChanged.connect(self.set_ballmode)

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
        """
        Docstring for toggle_matx

        :param self: Description
        """
        self._prefs.renderer_matx_enabled = (
            True if self._cbx_matx.isChecked() else False
        )

    def toggle_mantra(self):
        """
        En/Disable Renderer Mantra

        :param self: Description
        """
        self._prefs.renderer_mantra_enabled = (
            True if self._cbx_mantra.isChecked() else False
        )

    def toggle_arnold(self):
        """
        En/Disable Renderer Mantra

        :param self: Description
        """
        self._prefs.renderer_arnold_enabled = (
            True if self._cbx_arnold.isChecked() else False
        )

    def toggle_redshift(self):
        """
        En/Disable Renderer Mantra

        :param self: Description
        """
        self._prefs.renderer_redshift_enabled = (
            True if self._cbx_redshift.isChecked() else False
        )

    def toggle_octane(self):
        """
        En/Disable Renderer Mantra

        :param self: Description
        """
        self._prefs.renderer_octane_enabled = (
            True if self._cbx_octane.isChecked() else False
        )

    def set_rendersize(self):
        """
        Set Rendersize (Disk)

        :param self: Description
        """
        self._prefs.rendersize = self.line_rendersize.value()

    def set_thumbsize(self):
        """
        Set ThumbSize (View)
        :param self: Description
        """
        self._prefs.thumbsize = self.line_thumbsize.value()

    def set_rendersamples(self):
        """
        Set RenderSamples (Disk)

        :param self: Description
        """
        self._prefs.rendersamples = self.line_rendersamples.value()

    def set_ballmode(self):
        """
        Set Chosen Shaderball

        :param self: Description
        """
        self._prefs.ballmode = self._combo_ballmode.currentIndex()

    def set_render_on_import(self):
        """
        Set if Thumbnails should be rendered on import to MatLib

        :param self: Description
        """
        self._prefs.render_on_import = int(self.cbx_render_on_import.isChecked())

    def closeEvent(self, arg__1: QCloseEvent) -> None:
        """
        Save Preferences on Close

        :param self: Description
        :param arg__1: Description
        :type arg__1: QCloseEvent
        """
        self._prefs.save()

    # Fill UI
    def fill_values(self) -> None:
        """
        Fill UI

        :param self: Description
        """
        self.directory = self._prefs.dir
        self.rendersize = self._prefs.rendersize
        self.thumbsize = self._prefs.thumbsize
        self.render_on_import = self._prefs.render_on_import
        self.rendersamples = self._prefs.rendersamples
        self.ballmode = self._prefs.ballmode

        self.line_workdir.setText(self.directory)
        self.line_rendersize.setValue(self.rendersize)
        self.line_thumbsize.setValue(self.thumbsize)
        self.line_rendersamples.setValue(self.rendersamples)

        self._combo_ballmode.setCurrentIndex(self.ballmode)

        self.cbx_render_on_import.setChecked(self.render_on_import)

        self._cbx_matx.setChecked(self._prefs.renderer_matx_enabled)
        self._cbx_mantra.setChecked(self._prefs.renderer_mantra_enabled)
        self._cbx_arnold.setChecked(self._prefs.renderer_arnold_enabled)
        self._cbx_redshift.setChecked(self._prefs.renderer_redshift_enabled)
        self._cbx_octane.setChecked(self._prefs.renderer_octane_enabled)
