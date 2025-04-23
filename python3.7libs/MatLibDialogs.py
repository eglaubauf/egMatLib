import os

# PySide2
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2 import QtUiTools


###################################
######  THE USD DIALOG  ######
###################################
class usdDialog(QDialog):
    def __init__(self):
        super(usdDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.realpath(__file__))

        # Set Vars
        self.categories = None
        self.tags = None
        self.fav = False
        self.canceled = False

        ## LOAD UI
        ## Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QFile(self.script_path + "/Dialog.ui")
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainLayout)

        # Link Slots & Signals
        # FILTER UI
        self.line_cats = self.ui.findChild(QLineEdit, "line_categories")
        self.line_tags = self.ui.findChild(QLineEdit, "line_tags")
        self.cb_fav = self.ui.findChild(QCheckBox, "cb_fav")

        self.buttons = self.ui.findChild(QDialogButtonBox, "buttonBox")
        self.buttons.accepted.connect(self.confirm)
        self.buttons.rejected.connect(self.destroy)

    # Confirm material Creation
    def confirm(self):
        self.categories = self.line_cats.text()
        self.tags = self.line_tags.text()
        self.fav = self.cb_fav.isChecked()
        self.accept()

    # Cancel material Creation
    def destroy(self):
        self.canceled = True
        self.close()

    def reject(self):
        self.canceled = True
        self.close()


###################################
########  THE PREFS DIALOG ########
###################################


class PrefsDialog(QDialog):
    def __init__(self, library, prefs):
        super(PrefsDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.realpath(__file__))

        self.library = library
        self.prefs = prefs
        self.canceled = False

        ## LOAD UI
        ## Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QFile(self.script_path + "/PrefsMatLib.ui")
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # UI
        self.line_workdir = self.ui.findChild(QLineEdit, "line_workdir")
        self.line_thumbsize = self.ui.findChild(QLineEdit, "line_thumbsize")
        self.line_rendersize = self.ui.findChild(QLineEdit, "line_rendersize")
        self.cbx_renderOnImport = self.ui.findChild(QCheckBox, "cbx_renderOnImport")

        self.buttons = self.ui.findChild(QDialogButtonBox, "buttonBox")
        self.buttons.accepted.connect(self.confirm)
        self.buttons.rejected.connect(self.destroy)

        # Load Config from settings
        self.fill_values()

        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainLayout)

    # Apply Prefs Change
    def confirm(self):
        self.prefs.set_dir(self.line_workdir.text())
        self.prefs.save()

        self.library.set_renderSize(int(self.line_rendersize.text()))
        self.library.set_thumbSize(int(self.line_thumbsize.text()))
        self.library.set_renderOnImport(int(self.cbx_renderOnImport.isChecked()))

        self.library.save()
        self.accept()

    # Cancel Prefs Change
    def destroy(self):
        self.canceled = True
        self.close()

    # Fill UI
    def fill_values(self):
        self.directory = self.prefs.get_dir()
        self.rendersize = self.library.get_renderSize()
        self.thumbsize = self.library.get_thumbSize()
        self.renderOnImport = self.library.get_renderOnImport()

        self.line_workdir.setText(self.directory)
        self.line_rendersize.setText(str(self.rendersize))
        self.line_thumbsize.setText(str(self.thumbsize))
        self.cbx_renderOnImport.setChecked(self.renderOnImport)


class materialDialog(QDialog):
    def __init__(self):
        super(materialDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.realpath(__file__))

        # Set Vars
        self.categories = None
        self.tags = None
        self.fav = False
        self.canceled = False

        ## LOAD UI
        ## Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QFile(self.script_path + "/Dialog.ui")
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainLayout)

        # Link Slots & Signals
        # FILTER UI
        self.line_cats = self.ui.findChild(QLineEdit, "line_categories")
        self.line_tags = self.ui.findChild(QLineEdit, "line_tags")
        self.cb_fav = self.ui.findChild(QCheckBox, "cb_fav")
        self.cb_usd = self.ui.findChild(QCheckBox, "cb_usd")

        self.buttons = self.ui.findChild(QDialogButtonBox, "buttonBox")
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
    def destroy(self):
        self.canceled = True
        self.close()


class AboutDialog(QDialog):
    def __init__(self):
        super(AboutDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.realpath(__file__))

        ## LOAD UI
        ## Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QFile(self.script_path + "/About.ui")
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainLayout)
