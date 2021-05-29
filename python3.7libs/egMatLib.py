import sys
import os
import hou

# PySide2
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2 import QtUiTools


class egMatLibPanel(QtWidgets.QWidget):
    def __init__(self):
        super(egMatLibPanel, self).__init__()
        self.load_settings()
        scriptpath = os.path.dirname(os.path.realpath(__file__))

        ## Load UI from ui.file
        loader = QUiLoader()
        file = QtCore.QFile(scriptpath + '/MatLib.ui')
        file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # Load Ui Element so self
        self.menu = self.ui.findChild(QMenuBar, 'menubar')

        # Config
        self.thumbSize = 150

        # Link Buttons
        self.btn_update = self.ui.findChild(QPushButton, 'btn_update')
        self.btn_update.clicked.connect(self.loadMaterials)

        self.btn_delete = self.ui.findChild(QPushButton, 'btn_delete')
        self.btn_delete.clicked.connect(self.delete_material)

        self.btn_import = self.ui.findChild(QPushButton, 'btn_import')
        self.btn_import.clicked.connect(self.import_material)

        # Thumbnail list view from Ui
        self.thumblist = self.ui.findChild(QListWidget, 'listw_matview')
        self.thumblist.setIconSize(QSize(self.thumbSize, self.thumbSize))
        self.thumblist.setSpacing(1)
        #self.thumblist.setFlow()
        #self.thumblist.doubleClicked.connect(self.setTexture)
        #self.thumblist.clicked.connect(self.setLargePreview)
        #self.thumblist.installEventFilter(self)


        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)

        self.setLayout(mainLayout)
        self.create_default_icon()
        self.loadMaterials()

    def loadMaterials(self):
        # TODO: Load from Settings.json
        mat_dir = os.path.dirname("G:/Git/egMatLib/lib/")
        self.files = []
        for f in os.listdir(mat_dir):
            curr = os.path.join(mat_dir,f)
            if os.path.isfile(curr):
                curr = mat_dir + '/' + f
                if curr.endswith('.rsmat'):
                    self.files.append(curr)



        #  Now get all images for our Materials and List add them to the thumblist

        #  Dirty Empty for now
        self.thumblist.clear()  # TODO: Make nice and fast in the future by only changing new ones

        for f in self.files:
            img = f.replace('.rsmat', '.png')

            # Check if Thumb Exists and attach
            if os.path.isfile(img):
                pixmap = QPixmap.fromImage(QImage(img)).scaled(self.thumbSize, self.thumbSize, aspectMode=Qt.KeepAspectRatio)
                icon = QIcon(pixmap)
            else:
                icon = self.default_icon

            # Create entry in Thumblist
            img_name = img.rsplit('/', 1)[1][:-4]
            item = QListWidgetItem(icon, img_name)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            self.thumblist.addItem(item)
            self.thumblist.sortItems()


    def create_default_icon(self):
        #Generate Default Icon
        default_img = QImage(150, 150, QImage.Format_RGB16)
        default_img.fill(QColor(0, 0, 0))
        pixmap = QPixmap.fromImage(default_img).scaled(self.thumbSize, self.thumbSize, aspectMode=Qt.KeepAspectRatio)
        self.default_icon = QIcon(pixmap)

    #  Load Settings from Disk
    def load_settings(self):
        pass

    def filter_materials():
        pass

    def update_missing_materials(self):
        pass

    def update_all_materials(self):
        pass

    def update_single_material(self):
        pass

    def set_category(self):
        pass

    def delete_material(self):
        if hou.ui.displayConfirmation('This will delete the selected Material from Disk. Are you sure?'):
            print('Deleted')
        return

    def import_material(self):
        pass

    def save_material(self):
        pass
