import sys
import os
import hou
import time
import imghdr

# PySide2
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2 import QtUiTools


class egMatLibPanel(QWidget):
    def __init__(self):
        super(egMatLibPanel, self).__init__()
        self.load_settings()
        scriptpath = os.path.dirname(os.path.realpath(__file__))

        # Config
        self.thumbSize = 150
        self.extension = ".rsmat"
        self.img_extension = ".png"
        self.lib = os.path.dirname("G:/Git/egMatLib/lib/")

        ## Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QFile(scriptpath + '/MatLib.ui')
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # Load Ui Element so self
        self.menu = self.ui.findChild(QMenuBar, 'menubar')

        # Link Buttons
        self.btn_update = self.ui.findChild(QPushButton, 'btn_update')
        self.btn_update.clicked.connect(self.update_single_material)

        self.btn_save = self.ui.findChild(QPushButton, 'btn_save')
        self.btn_save.clicked.connect(self.save_material)

        self.btn_delete = self.ui.findChild(QPushButton, 'btn_delete')
        self.btn_delete.clicked.connect(self.delete_material)

        self.btn_import = self.ui.findChild(QPushButton, 'btn_import')
        self.btn_import.clicked.connect(self.import_material)

        # Thumbnail list view from Ui
        self.thumblist = self.ui.findChild(QListWidget, 'listw_matview')
        self.thumblist.setIconSize(QSize(self.thumbSize, self.thumbSize))
        self.thumblist.doubleClicked.connect(self.import_material)

        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)

        self.setLayout(mainLayout)
        self.create_default_icon()
        self.loadMaterials()


    def loadMaterials(self):
        # TODO: Load from Settings.json

        self.files = []
        for f in os.listdir(self.lib):
            curr = os.path.join(self.lib,f)
            if os.path.isfile(curr):
                curr = self.lib + '/' + f
                if curr.endswith(self.extension):
                    self.files.append(curr)

        #  Now get all images for our Materials and List add them to the thumblist
        #  Dirty Empty for now
        self.thumblist.clear()  # TODO: Make nice and fast in the future by only changing new ones
        for f in self.files:
            img = f.replace(self.extension, self.img_extension)

            # Check if Thumb Exists and attach
            if os.path.isfile(img):
                pixmap = QPixmap.fromImage(QImage(img)).scaled(self.thumbSize, self.thumbSize, aspectMode=Qt.KeepAspectRatio)
                icon = QIcon(pixmap)
            else:
                icon = self.default_icon

            # Create entry in Thumblist
            img_name = img.rsplit('/', 1)[1][:-4]
            item = QListWidgetItem(icon, img_name)
            #item.addRoleName()
            #item.setData(Qt.UserRole, f)  # add Filepath to Item
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

        item = self.get_selected_material_from_lib()
        if not item:
            return

        builder = self.import_material()
        self.save_node(builder)
        return

    def set_category(self):
        pass


    def delete_material(self):

        if not hou.ui.displayConfirmation('This will delete the selected Material from Disk. Are you sure?'):
            return

        item = self.get_selected_material_from_lib()
        if not item:
            return

        file_path = self.lib + "/" + item.text()
        if os.path.exists(file_path + self.extension ):
            os.remove(file_path + self.extension)
        if os.path.exists(file_path + self.img_extension ):
            os.remove(file_path + self.img_extension)

        self.loadMaterials()
        hou.ui.displayMessage("Material deleted")
        return


    #  Import Material to Scene
    def import_material(self):

        item = self.thumblist.selectedItems()[0]
        if not item:
            hou.ui.displayMessage("No Material selected")
            return

        file_name = self.lib + "/" + item.text() + self.extension

        # CreateBuilder
        builder = hou.node('/mat').createNode('redshift_vopnet')
        builder.setName(item.text(), unique_name=True)

        # Delete Default children in RS-VopNet
        for node in builder.children():
            node.destroy()
        # Load File
        builder.loadItemsFromFile(file_name, ignore_load_warnings=False)
        # MakeFancyPos
        builder.moveToGoodPosition()
        return builder


    def get_selected_material_from_lib(self):
        item = self.thumblist.selectedItems()[0]
        if not item:
            hou.ui.displayMessage("No Material selected")
            return None
        return item


    #  Saves a Node to the Library
    def save_material(self):

        sel = hou.selectedNodes()
        # Check selection
        if not sel:
            hou.ui.displayMessage('No Material selected')
            return
        self.save_node(sel[0])
        return

    #  Saves a Node to the Library
    def save_node(self, node):

        # Check against NodeType

        if node.type().name() != "redshift_vopnet":
            hou.ui.displayMessage('Selected Node is not a Material Builder')
            return

        # Filepath where to save stuff
        name = node.name()
        file_name = self.lib + "/" + name + self.extension

        children = node.children()
        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # Create Thumbnail
        thumb = hou.node("/obj").createNode("eg_thumbnail")

        thumb.parm("mat").set(node.path())

        # Build path
        path = self.lib + '/' + name + self.img_extension
        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path)
        exclude = "* ^" + thumb.name()
        thumb.parm("obj_exclude").set(exclude)
        lights = thumb.name() + "/*"
        thumb.parm("lights").set(lights)
        thumb.parm("render").pressButton()

        # Wait until Render is finished
        self.waitForRender(path)
        # while not imghdr.what(path):
        #     self.waitForRender(path)  # Check if file is valid

        # CleanUp
        thumb.destroy()

        # Reload Library
        self.loadMaterials()

        # OK, bye
        msg = "Material " + name + " created"
        hou.ui.displayMessage(msg)
        return

    def waitForRender(self, path):
        mustend = time.time() + 60.0
        while time.time() < mustend:
            if os.path.exists(path):
               return True
            time.sleep(0.5)
        return False
