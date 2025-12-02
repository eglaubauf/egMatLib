import os

from PySide6 import QtWidgets, QtCore, QtUiTools


class AboutDialog(QtWidgets.QDialog):
    def __init__(self):
        super(AboutDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        # Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QtCore.QFile(self.script_path + "/ui/about.ui")
        file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # set main layout and attach to widget
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.ui)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainLayout)
