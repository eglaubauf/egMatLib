import sys
import os
import hou
import time
import imghdr
import json
import uuid

# PySide2
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2 import QtUiTools


class egMatLibPanel(QWidget):
    def __init__(self):
        super(egMatLibPanel, self).__init__()
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        #Initialize
        self.lib = self.script_path[:-14] + "/lib/"
        self.lib = self.lib.replace("\\", "/")

        # Config
        self.config = self.load_library()

        #Load Settings
        self.thumbSize = self.config["settings"][0]["thumbsize"]
        self.extension = self.config["settings"][0]["extension"]
        self.img_extension = self.config["settings"][0]["img_extension"]  # TODO: Make EXRs work at some point, needs convertion for PixMap to 8 Bit
        self.done_file = self.config["settings"][0]["done_file"]

        self.materials = self.config["materials"]
        self.categories = self.config["categories"]
        self.tags = self.config["tags"]
        self.selected_cat = None
        self.filter = ""
        self.draw_mats = self.materials

        self.createView()
        self.update_view()


    ###################################
    ########### VIEW STUFF ############
    ###################################

    def createView(self):

        ## Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QFile(self.script_path + '/MatLib.ui')
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

        # Category UI
        self.cat_list = self.ui.findChild(QListWidget, 'listw_catview')
        self.cat_list.clicked.connect(self.update_selected_cat)

        self.btn_add_cat = self.ui.findChild(QPushButton, 'btn_add_cat')
        self.btn_add_cat.clicked.connect(self.add_category_user)

        self.btn_rmv_cat = self.ui.findChild(QPushButton, 'btn_rmv_cat')
        self.btn_rmv_cat.clicked.connect(self.rmv_category_user)

        # FILTER UI
        self.line_filter = self.ui.findChild(QLineEdit, 'line_filter')
        self.line_filter.textChanged.connect(self.filter_thumb_view_user)

        # Details UI
        self.details = self.ui.findChild(QTableWidget, 'widget_detail')

        # Default icon for rendering
        self.create_default_icon()

        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)

        self.update_cat_view()
        self.setLayout(mainLayout)


    ###################################
    ########### JSON STUFF ############
    ###################################

    # Load Library from JSON
    def load_library(self):
        with open(self.lib+("/library.json")) as lib_json:
            return json.load(lib_json)


    # Save Library to JSON
    def save_library(self):
        # Update actual config data
        self.config["materials"] = self.materials
        self.config["categories"] = self.categories
        self.config["tags"] = self.tags

        with open(self.lib+("/library.json"), "w") as lib_json:
            return json.dump(self.config, lib_json, indent=4)


    ###################################
    ########### USER STUFF ############
    ###################################

    # User Adds Category with Button
    def add_category_user(self):
        choice, cat = hou.ui.readInput("Please enter the new category name:")
        if choice:
            print("Yes")
            return
        self.check_add_category(cat)
        self.save_library()
        self.update_cat_view()
        self.update_view()
        return

    # User Removes Category with Button
    def rmv_category_user(self):
        rmv_item = self.cat_list.selectedItems()
        self.categories.remove(rmv_item[0].text())

        #check materials against category and remove there also:
        for mat in self.materials:
            if rmv_item[0].text() in mat["categories"]:
                mat["categories"].remove(rmv_item[0].text())

        self.save_library()
        self.update_cat_view()
        self.update_view()
        return

    # Get Filter Text from User
    def filter_thumb_view_user(self):
        self.filter = self.line_filter.text()
        self.update_view()
        return

    ###################################
    ########## UPDATE VIEWS ###########
    ###################################



    # Update the Views when selection changes
    def update_selected_cat(self):
        self.selected_cat = None
        items = self.cat_list.selectedItems()
        # Only one item selected
        if len(items) == 1:
            if items[0].text() == "All":
                self.selected_cat = None
                self.update_view()
                return
            else:
                self.selected_cat = items[0].text()
                self.update_view()
                return
        # Multiple items selected
        # for i in items:
        #     if i.text() == "All":
        #         self.selected_cat = None
        #         self.update_view()
        #         return
        #     self.selected_cat.append(i.text())
        # self.update_view()
        return


    # Update Category View
    def update_cat_view(self):

        self.cat_list.clear()
        for cat in self.categories:
            item = QListWidgetItem(cat)
            self.cat_list.addItem(item)

        self.thumblist.sortItems()

        return


    # Filter Materials in Thumblist for Category
    def filter_view_category(self):
        # Filter Thumbnail View
        self.draw_mats = []
        for mat in self.materials:
            if self.selected_cat in mat['categories']:
                self.draw_mats.append(mat)
        if not self.selected_cat:
            self.draw_mats = self.materials
        return


    # Filter Materials in Thumblist for Category
    def filter_view_filter(self):
        # Filter Thumbnail View

        if self.filter is "":
            return
        tmp = []
        for mat in self.draw_mats:
            if self.filter in mat["name"]:
                tmp.append(mat)
        self.draw_mats = tmp
        return


    # Update Thumbnail View
    def update_view(self):
        # Cleanup UI
        self.thumblist.clear()

        self.filter_view_category()  # Filter View by Category
        self.filter_view_filter()  # Filter View by Line Filter
        if self.draw_mats:
            for mat in self.draw_mats:
                img = self.lib + mat["name"] + self.img_extension

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
                item.setData(Qt.UserRole, mat["id"])  # Store ID with Thumb
                self.thumblist.addItem(item)
                self.thumblist.sortItems()



    # Create PlaceHolder Icon in case something goes wrong
    def create_default_icon(self):
        #Generate Default Icon
        default_img = QImage(150, 150, QImage.Format_RGB16)
        default_img.fill(QColor(0, 0, 0))
        pixmap = QPixmap.fromImage(default_img).scaled(self.thumbSize, self.thumbSize, aspectMode=Qt.KeepAspectRatio)
        self.default_icon = QIcon(pixmap)


    # Rerender Selected Material
    def update_single_material(self):
        item = self.get_selected_material_from_lib()
        if not item:
            return

        builder = self.import_material()
        self.save_node(builder)
        builder.destroy()
        return



    ###################################
    ######### LIBRARY STUFF ###########
    ###################################


    # Delete Material from Library
    def delete_material(self):
        if not hou.ui.displayConfirmation('This will delete the selected Material from Disk. Are you sure?'):
            return

        item = self.get_selected_material_from_lib()
        if not item:
            return
        id = item.data(Qt.UserRole)

        for mat in self.materials:
            if mat["id"] == id:
                # Remove files from Library
                self.materials.remove(mat)
                self.save_library()

                # Remove Files from Disk
                file_path = self.lib + item.text()
                if os.path.exists(file_path + self.extension ):
                    os.remove(file_path + self.extension)
                if os.path.exists(file_path + self.img_extension ):
                    os.remove(file_path + self.img_extension)

                # Update View
                self.update_view()
        return


    # Get the selected Material from Library
    def get_selected_material_from_lib(self):
        item = self.thumblist.selectedItems()[0]
        if not item:
            hou.ui.displayMessage("No Material selected")
            return None
        return item


    # Check if Category already exits in Library
    def check_add_category(self, cat):
        if not cat in self.categories:
            self.categories.append(cat)
        return


    # Check if Tags already exits in Library
    def check_add_tags(self, tag):
        if not tag in self.tags:
            self.tags.append(tag)
        return


    #  Saves a Material to the Library
    def save_material(self):
        # Get Selected from Network View
        sel = hou.selectedNodes()
        # Check selection
        if not sel:
            hou.ui.displayMessage('No Material selected')
            return
        # Get Category from User
        choice, cat = hou.ui.readInput("Add Object to Categories (Comma Separated")
        if choice:
            return
        self.check_add_category(cat)

        # Get Category from User
        choice, tag = hou.ui.readInput("Add Object to Tags (Comma Separated)")
        if choice:
            return
        self.check_add_tags(tag)

        # Add Fav Yes/No
        fav = int(hou.ui.displayConfirmation("Do you want this to be a Favorite?"))

        # Add Material to Library
        if self.save_node(sel[0]):
            # Format
            id = uuid.uuid1().time
            name = sel[0].name()
            cats = cat.split(",")
            tags = tag.split(",")

            material = {"id": id, "name": name, "categories": cats, "tags": tags, "favorite": fav}
            self.materials.append(material)
            self.save_library()
            self.update_view()
        return



    ###################################
    ########### DISK STUFF ############
    ###################################



    #  Render Image & Node-tree to disk
    def save_node(self, node):
        # Check against NodeType
        if node.type().name() != "redshift_vopnet":
            hou.ui.displayMessage('Selected Node is not a Material Builder')
            return False

        # Filepath where to save stuff
        file_name = self.lib + node.name() + self.extension

        children = node.children()
        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # Create Thumbnail
        thumb = hou.node("/obj").createNode("eg_thumbnail")
        thumb.parm("mat").set(node.path())

        # Build path
        path = self.lib + node.name() + self.img_extension
        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path)
        exclude = "* ^" + thumb.name()
        thumb.parm("obj_exclude").set(exclude)
        lights = thumb.name() + "/*"
        thumb.parm("lights").set(lights)

        # Make sure there is no done file
        if os.path.exists(self.lib + self.done_file):
            os.remove(self.lib + self.done_file)

        # Render Frame
        thumb.parm("render").pressButton()

        # Wait until Render is finished
        self.waitForRender(path)

        # CleanUp
        thumb.destroy()

        return True

    # Wait until Background Rendering is finished
    def waitForRender(self, path):
        mustend = time.time() + 60.0
        while time.time() < mustend:
            if os.path.exists(self.lib + self.done_file):
                os.remove(self.lib + self.done_file)
                return True
            time.sleep(0.5)
        return False


    #  Import Material to Scene
    def import_material(self):

        item = self.thumblist.selectedItems()[0]
        if not item:
            hou.ui.displayMessage("No Material selected")
            return

        file_name = self.lib + item.text() + self.extension

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