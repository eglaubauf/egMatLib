import os
import hou
import time
import json
import uuid

# PySide2
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2 import QtUiTools

# This holds the global settings
class prefs():
    def __init__(self):
        # TODO: Replace with HOU ENV
        self.path = "G:/Git/egMatLib"
        self.data = {}
        self.load()

    def save(self):

        self.data["directory"] = self.directory
        self.data["showButtons"] = self.show_buttons
        self.data["extension"] = self.ext
        self.data["img_extension"] = self.img_ext
        self.data["done_file"] = self.done_file
        self.data["mat_dir"] = self.mat_dir
        self.data["img_dir"] = self.img_dir

        with open(self.path+("/settings.json"), "w") as lib_json:
            json.dump(self.data, lib_json, indent=4)

    def load(self):
        with open(self.path+("/settings.json")) as lib_json:
            data = json.load(lib_json)

            self.directory = data["directory"]
            self.show_buttons = data["showButtons"]
            self.ext = data["extension"]
            self.img_ext = data["img_extension"]
            self.done_file = data["done_file"]
            self.mat_dir = data["mat_dir"]
            self.img_dir = data["img_dir"]
        return

    def get_dir(self):
        return self.directory

    def get_img_dir(self):
        return self.img_dir

    def get_mat_dir(self):
        return self.mat_dir

    def get_img_ext(self):
        return self.img_ext

    def get_ext(self):
        return self.ext

    def get_done_file(self):
        return self.done_file

    def get_btns(self):
        return self.show_buttons

    def set_btns(self, val):
        self.show_buttons = val

    def set_dir(self, val):
        self.directory = val


# This holds a Library
class eg_library():
    def __init__(self):
        self.materials = None
        self.categories = None
        self.tags = None
        self.settings = None
        self.path = None

    def load(self, path, prefs):
        self.path = path
        with open(self.path+("/library.json")) as lib_json:
            self.data = json.load(lib_json)

            self.materials = self.data["materials"]
            self.categories = self.data["categories"]
            self.tags = self.data["tags"]
            self.thumbsize = self.data["thumbsize"]
            self.rendersize = self.data["rendersize"]
        self.settings = prefs
        return

    def save(self):
        # Update actual config data
        self.data["materials"] = self.materials
        self.data["categories"] = self.categories
        self.data["tags"] = self.tags
        self.data["thumbsize"] = self.thumbsize
        self.data["rendersize"] = self.rendersize

        with open(self.path+("/library.json"), "w") as lib_json:
            json.dump(self.data, lib_json, indent=4)
        return

    def get_path(self):
        return self.path

    def get_materials(self):
        return self.materials

    def get_categories(self):
        return self.categories

    def get_tags(self):
        return self.tags

    def get_thumbSize(self):
        return self.thumbsize

    def set_thumbSize(self, val):
        self.thumbsize = val

    def set_renderSize(self, val):
        self.rendersize = val

    def get_renderSize(self):
        return self.rendersize

    def remove_material(self, id):
        for mat in self.materials:
            if id == mat["id"]:
                self.materials.remove(mat)

                # Remove Files from Disk
                file_path = self.path + str(id)
                if os.path.exists(file_path + self.settings.get_mat_dir() + self.settings.get_ext()):
                    os.remove(file_path + self.settings.get_mat_dir() + self.settings.get_ext())
                if os.path.exists(file_path + self.settings.get_img_dir() + self.settings.get_img_ext()):
                    os.remove(file_path + self.settings.get_img_dir() + self.settings.get_img_ext())
                self.save()
                return

    # Check if Category already exits in Library
    def check_add_category(self, cat):
        cats = cat.split(",")
        for c in cats:
            c = c.replace(" ", "")
            if c != "":
                if c not in self.categories:
                    self.categories.append(c)
        return


    def check_add_tags(self, tags):
        tags = tags.split(",")
        for t in tags:
            t = t.replace(" ", "")
            if t != "":
                if t not in self.tags:
                    self.tags.append(t)
        return


    def add_material(self, node, cats, tags, fav):

        id = uuid.uuid1().time
        if self.save_node(node, id):
            # Format
            name = node.name()
            name.replace(" ", "")

            cats = cats.split(",")
            for c in cats:
                c.replace(" ", "")

            tags = tags.split(",")
            for t in tags:
                t.replace(" ", "")

            material = {"id": id, "name": name, "categories": cats, "tags": tags, "favorite": fav, "renderer": "Redshift"}
            self.materials.append(material)
            self.save()
        return

    def import_material(self, id):

        file_name = self.get_path() + self.settings.get_mat_dir() + str(id) + self.settings.get_ext()

        mat = self.get_material_by_id(id)

        # CreateBuilder
        builder = hou.node('/mat').createNode('redshift_vopnet')
        builder.setName(mat["name"], unique_name=True)

        # Delete Default children in RS-VopNet
        for node in builder.children():
            node.destroy()
        # Load File
        try:
            builder.loadItemsFromFile(file_name, ignore_load_warnings=False)
        except:
            hou.ui.displayMessage("File not Found on Disk")
            return
        # MakeFancyPos
        builder.moveToGoodPosition()
        return builder


    #  Render Image & Node-tree to disk
    def save_node(self, node, id):
        # Check against NodeType
        if node.type().name() != "redshift_vopnet":
            hou.ui.displayMessage('Selected Node is not a Material Builder')
            return False

        # Filepath where to save stuff
        file_name = self.get_path() + self.settings.get_mat_dir() + str(id) + self.settings.get_ext()

        children = node.children()
        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # Create Thumbnail
        thumb = hou.node("/obj").createNode("eg_thumbnail")
        thumb.parm("mat").set(node.path())

        # Build path
        path = self.get_path()  + self.settings.get_img_dir() + str(id) + self.settings.get_img_ext()

        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path)
        exclude = "* ^" + thumb.name()
        thumb.parm("obj_exclude").set(exclude)
        lights = thumb.name() + "/*"
        thumb.parm("lights").set(lights)

        # Make sure there is no done file
        if os.path.exists(self.get_path() + self.settings.get_done_file()):
            os.remove(self.get_path() + self.settings.get_done_file())

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
            if os.path.exists(self.get_path() + self.settings.get_done_file()):
                os.remove(self.get_path() + self.settings.get_done_file())
                return True
            time.sleep(0.5)
        return False


    # Remove Category from Library
    def remove_category(self, cat):
        self.categories.remove(cat)
        # check materials against category and remove there also:
        for mat in self.materials:
            if cat in mat["categories"]:
                mat["categories"].remove(cat)
        return

    def rename_category(self, old, new):
        # Update Categories with that name
        for count, current in enumerate(self.categories):
            if current == old:
                self.categories[count] = new
        # Update all Categories with that name in all Materials
        for j, mat in enumerate(self.materials):
            if old in mat["categories"]:
                for i, c in enumerate(mat["categories"]):
                    if c == old:
                        self.materials[j]["categories"][i] = new

        return

    # Set Material Name for Material with given ID
    def set_material_name(self, id, name):
        mat = self.get_material_by_id(id)
        mat["name"] = name

    # Get Material by ID
    def get_material_by_id(self, id):
        for mat in self.materials:
            if int(id) == mat["id"]:
                return mat
        return None

    # Set Material Category for Material with given ID
    def set_material_cat(self, id, cat):
        self.check_add_category(cat)
        mat = self.get_material_by_id(id)

        cats = cat.split(",")
        for c in cats:
            c = c.replace(" ", "")
        mat["categories"] = cats
        return

    # Set Material Tag for Material with given ID
    def set_material_tag(self, id, tag):
        mat = self.get_material_by_id(id)
        tags = tag.split(",")
        for t in tags:
            t = t.replace(" ", "")
        mat["tags"] = tags
        return

# The PythonPanel
class egMatLibPanel(QWidget):
    def __init__(self):
        super(egMatLibPanel, self).__init__()

        #Initialize
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        path = self.script_path[:-14] + "/lib/"
        path = path.replace("\\", "/")

        # Config
        self.prefs = prefs()

        # Create Library
        self.library = eg_library()
        self.library.load(path, self.prefs)

        self.selected_cat = None
        self.filter = ""
        self.draw_mats = self.library.get_materials() # Filtererd Materials for Views

        self.createView()
        self.update_views()


    def update_views(self):
        self.update_thumb_view()
        self.update_cat_view()
        return

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

        #Helper for Table_Trigger
        self.active = False

        # Load Ui Element so self
        self.menu = self.ui.findChild(QMenuBar, 'menubar')
        self.menuGoto = self.ui.findChild(QMenu, 'menu_file')
        self.action_prefs = self.ui.findChild(QAction, 'action_prefs')
        self.action_prefs.triggered.connect(self.show_prefs)

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
        self.thumblist.setIconSize(QSize(self.library.get_thumbSize(), self.library.get_thumbSize()))
        self.thumblist.doubleClicked.connect(self.import_material)
        self.thumblist.itemPressed.connect(self.update_details_view)
        self.thumblist.setGridSize(QSize(self.library.get_thumbSize()+10, self.library.get_thumbSize()+40))
        self.thumblist.setSortingEnabled(True)

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
        self.details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.details.setColumnWidth(0,120)
        self.details.setColumnWidth(1,200)
        self.details.setRowHidden(4, True)
        self.details.setRowHidden(3, True) # TODO: Implement Favs, for now just hidden

        self.details.itemChanged.connect(self.update_entry_from_detail)
        self.details.itemDoubleClicked.connect(self.listen_entry_from_detail)


        # RC Menus
        self.thumblist.customContextMenuRequested.connect(self.thumblist_rc_menu)
        self.cat_list.customContextMenuRequested.connect(self.catlist_rc_menu)

        # Default icon for rendering
        self.create_default_icon()

        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainLayout)


    ###################################
    ############ RC MENUS #############
    ###################################

    def thumblist_rc_menu(self):
        cmenu = QMenu(self)

        delAct = cmenu.addAction("Delete Entry")
        renderAct = cmenu.addAction("Rerender Thumbnail")
        importAct = cmenu.addAction("Import to Scene")
        renderAllAct = cmenu.addAction("Render All Thumbnails")
        action = cmenu.exec_(QCursor.pos())

        #print(self)
        if action == delAct:
            self.delete_material()
        elif action == renderAct:
            self.update_single_material()
        elif action == importAct:
            self.import_material()
        elif action == renderAllAct:
            self.update_all_materials()
        return


    def catlist_rc_menu(self):
        cmenu = QMenu(self)

        removeAct = cmenu.addAction("Remove Category")
        renameAct = cmenu.addAction("Rename Entry")
        addAct = cmenu.addAction("Add Category")
        action = cmenu.exec_(QCursor.pos())

        #print(self)
        if action == removeAct:
            self.rmv_category_user()
            pass
        elif action == renameAct:
            self.rename_category_user()
            pass
        elif action == addAct:
            self.add_category_user()
        return


    ###################################
    ########### USER STUFF ############
    ###################################


    def show_prefs(self):

        prefs = PrefsDialog(self.library, self.prefs)
        prefs.exec_()

        if prefs.canceled:
            return

        #if dialog.categories:
            #self.library.check_add_category(dialog.categories)
        #if dialog.tags:
            #self.library.check_add_tags(dialog.tags)
        # if dialog.fav:
        #     fav = dialog.fav
        # TODO: Implement Favs
        # fav = int(hou.ui.displayConfirmation("Do you want this to be a Favorite?"))

        #self.library.add_material(sel[0] ,dialog.categories, dialog.categories, dialog.fav)
        self.update_views()
        return


        pass

    # User Adds Category with Button
    def add_category_user(self):
        choice, cat = hou.ui.readInput("Please enter the new category name:")
        if choice: # Return if no
            return
        self.library.check_add_category(cat)
        self.library.save()
        self.update_views()
        return

    # User Removes Category with Button
    def rmv_category_user(self):
        rmv_item = self.cat_list.selectedItems()
        # Prevent Deletion of "All" - Category
        if rmv_item[0].text() == "All":
            return

        self.library.remove_category(rmv_item[0].text())

        self.library.save()
        self.update_views()
        return


    def rename_category_user(self):

        choice, cat = hou.ui.readInput("Please enter the new category name:")
        if choice: # Return if no
            return
        # TODO: Check if Cat allready exists
        # if cat == "All":
        #     return

        rnm_item = self.cat_list.selectedItems()
        # Prevent Deletion of "All" - Category
        if rnm_item[0].text() == "All":
            return

        self.library.rename_category(rnm_item[0].text(), cat)

        self.library.save()
        self.update_views()
        return


    # Get Filter Text from User
    def filter_thumb_view_user(self):
        self.filter = self.line_filter.text()
        self.update_thumb_view()
        return

    def listen_entry_from_detail(self, item):
        # now in entry mode
        self.active = True
        self.active_item = item
        return

    def update_entry_from_detail(self, item):
        if self.active and self.active_item is item:
            curr_id = self.details.item(4,1).text()
            if item.row() == 0:
                # Change Name
                self.library.set_material_name(curr_id, item.text())
            elif item.row() == 1:
                self.library.set_material_cat(curr_id, item.text())
            elif item.row() == 2:
                self.library.set_material_tag(curr_id, item.text())
            elif item.row() == 3:
                #Change Fav
                # if item.CheckState() is Qt.Checked:
                #     item.setCheckState(Qt.Unchecked)
                # else:
                #     item.setCheckState(Qt.Checked)
                pass
            # Update All
            self.library.save()
            self.update_views()
            # Reset
            self.active = False
        return

    ###################################
    ########## UPDATE VIEWS ###########
    ###################################

    # Update Details view
    def update_details_view(self, item):

        if item is None:
            return
        id = self.get_id_from_thumblist(item)


        for mat in self.library.get_materials():
            if mat["id"] == id:
                # set name
                table_item = self.details.item(0,1)
                table_item.setText(mat["name"])
                # set cat
                table_item = self.details.item(1,1)
                table_item.setText(", ".join(mat["categories"]))
                # set tag
                table_item = self.details.item(2,1)
                table_item.setText(", ".join(mat["tags"]))
                # set fav
                table_item = self.details.item(3,1)
                if mat["favorite"] == 1:
                    table_item.setCheckState(Qt.Checked)
                else:
                    table_item.setCheckState(Qt.Unchecked)
                    #table_item.setText(mat["favorite"]))
                # set id
                table_item = self.details.item(4,1)
                table_item.setText(str(mat["id"]))
                # set Renderer
                table_item = self.details.item(5,1)
                table_item.setText(mat["renderer"])
        #Resize
        self.details.resizeColumnToContents(1)
        if self.details.columnWidth(1) < 200:
            self.details.setColumnWidth(1,200)
        return

    # Update the Views when selection changes
    def update_selected_cat(self):
        self.selected_cat = None
        items = self.cat_list.selectedItems()
        if len(items) == 1:
            if items[0].text() == "All":
                self.selected_cat = None
                self.update_thumb_view()
                return
            else:
                self.selected_cat = items[0].text()
                self.update_thumb_view()
                return
        return

    # Update Category View
    def update_cat_view(self):
        self.cat_list.clear()
        for cat in self.library.get_categories():
            item = QListWidgetItem(cat)
            self.cat_list.addItem(item)

        begin = self.cat_list.findItems("All", Qt.MatchExactly)[0]

        begin.setText("___All")
        self.cat_list.sortItems()
        begin.setText("All")
        self.thumblist.sortItems()

        return

    # Filter Materials in Thumblist for Category
    def filter_view_category(self):
        # Filter Thumbnail View
        self.draw_mats = []
        for mat in self.library.get_materials():
            if self.selected_cat in mat['categories']:
                self.draw_mats.append(mat)
        if not self.selected_cat:
            self.draw_mats = self.library.get_materials()
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
    def update_thumb_view(self):
        # Cleanup UI
        self.thumblist.clear()

        self.filter_view_category()  # Filter View by Category
        self.filter_view_filter()  # Filter View by Line Filter

        if self.draw_mats:
            for mat in self.draw_mats:
                img = self.library.get_path() + self.prefs.get_img_dir() + str(mat["id"]) + self.prefs.get_img_ext()

                # Check if Thumb Exists and attach
                if os.path.isfile(img):
                    pixmap = QPixmap.fromImage(QImage(img)).scaled(self.library.get_thumbSize(), self.library.get_thumbSize(), aspectMode=Qt.KeepAspectRatio)
                    icon = QIcon(pixmap)
                else:
                    icon = self.default_icon

                # Create entry in Thumblist
                #img_name = self.get_material_by_id(mat["id"])
                item = QListWidgetItem(icon, mat["name"])
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
                item.setData(Qt.UserRole, mat["id"])  # Store ID with Thumb
                self.thumblist.addItem(item)
                self.thumblist.sortItems()


    # Create PlaceHolder Icon in case something goes wrong
    def create_default_icon(self):
        #Generate Default Icon
        default_img = QImage(self.library.get_thumbSize(), self.library.get_thumbSize(), QImage.Format_RGB16)
        default_img.fill(QColor(0, 0, 0))
        pixmap = QPixmap.fromImage(default_img).scaled(self.library.get_thumbSize(), self.library.get_thumbSize(), aspectMode=Qt.KeepAspectRatio)
        self.default_icon = QIcon(pixmap)


    # Rerender All Visible Materials
    def update_all_materials(self):
        if not hou.ui.displayConfirmation('This can take a long time to render. Houdini will not be responsive during that time. Do you want continue rendering all visible Materials?'):
            return

        for i in range(self.thumblist.count()):
            item = self.thumblist.item(i)

            id = self.get_id_from_thumblist(item)
            builder = self.import_material(item)

            self.library.save_node(builder, id)
            builder.destroy()
        self.update_thumb_view()
        hou.ui.displayMessage("Rendering finished")
        return

    # Rerender Selected Material
    def update_single_material(self):
        item = self.get_selected_material_from_thumblist()
        if not item:
            return
        builder = self.import_material()
        id = self.get_id_from_thumblist(item)
        self.library.save_node(builder, id)
        self.update_thumb_view()
        builder.destroy()
        hou.ui.displayMessage("Thumbnail updated")
        return


    ###################################
    ######### LIBRARY STUFF ###########
    ###################################

    def get_id_from_thumblist(self, item):
        return item.data(Qt.UserRole)

    # Delete Material from Library
    def delete_material(self):
        if not hou.ui.displayConfirmation('This will delete the selected Material from Disk. Are you sure?'):
            return

        item = self.get_selected_material_from_thumblist()
        if not item:
            return

        id = self.get_id_from_thumblist(item)
        self.library.remove_material(id)

        # Update View
        self.update_thumb_view()
        return


    # Get the selected Material from Library
    def get_selected_material_from_thumblist(self):
        item = self.thumblist.selectedItems()[0]
        if not item:
            hou.ui.displayMessage("No Material selected")
            return None
        return item

    #  Saves a Material to the Library
    def save_material(self):
        # Get Selected from Network View
        sel = hou.selectedNodes()
        # Check selection
        if not sel:
            hou.ui.displayMessage('No Material selected')
            return
        self.get_material_info_user(sel)
        return

    def get_material_info_user(self, sel):
        # Get Stuff from User
        dialog = materialDialog()
        dialog.exec_()

        if dialog.canceled:
            return

        if dialog.categories:
            self.library.check_add_category(dialog.categories)
        if dialog.tags:
            self.library.check_add_tags(dialog.tags)
        # if dialog.fav:
        #     fav = dialog.fav
        # TODO: Implement Favs
        # fav = int(hou.ui.displayConfirmation("Do you want this to be a Favorite?"))

        self.library.add_material(sel[0] ,dialog.categories, dialog.tags, dialog.fav)
        self.update_views()
        return


    ###################################
    ########### DISK STUFF ############
    ###################################

    #  Import Material to Scene
    def import_material(self, sel=None):

        if not sel:
            item = self.thumblist.selectedItems()[0]
        else:
            item = sel

        if not item:
            hou.ui.displayMessage("No Material selected")
            return

        id = self.get_id_from_thumblist(item)
        return self.library.import_material(id)


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
        file = QFile(self.script_path + '/Dialog.ui')
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
        self.line_cats = self.ui.findChild(QLineEdit, 'line_categories')
        self.line_tags = self.ui.findChild(QLineEdit, 'line_tags')
        self.cb_fav = self.ui.findChild(QCheckBox, "cb_fav")

        self.buttons = self.ui.findChild(QDialogButtonBox, "buttonBox")
        self.buttons.accepted.connect(self.confirm)
        self.buttons.rejected.connect(self.destroy)


    def confirm(self):
        self.categories = self.line_cats.text()
        self.tags = self.line_tags.text()
        self.fav = self.cb_fav.isChecked()
        self.accept()

    def destroy(self):
        self.canceled = True
        self.close()


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
        file = QFile(self.script_path + '/Prefs.ui')
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # UI
        self.line_workdir = self.ui.findChild(QLineEdit, 'line_workdir')
        self.line_thumbsize = self.ui.findChild(QLineEdit, 'line_thumbsize')
        self.line_rendersize = self.ui.findChild(QLineEdit, 'line_rendersize')
        self.cb_buttons = self.ui.findChild(QCheckBox, "cb_buttons")

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


    def confirm(self):
        self.prefs.set_dir(self.line_workdir.text())
        self.prefs.set_btns(int(self.cb_buttons.isChecked()))
        self.prefs.save()

        self.library.set_renderSize(int(self.line_rendersize.text()))
        self.thumbsize = self.library.set_thumbSize(int(self.line_thumbsize.text()))
        self.library.save()

        self.accept()


    def destroy(self):
        self.canceled = True
        self.close()


    def fill_values(self):

        self.directory = self.prefs.get_dir()
        self.show_buttons =  self.prefs.get_btns()

        self.rendersize = self.library.get_renderSize()
        self.thumbsize = self.library.get_thumbSize()

        self.line_workdir.setText(self.directory)
        self.line_rendersize.setText(str(self.rendersize))
        self.line_thumbsize.setText(str(self.thumbsize))
        if self.show_buttons:
            self.cb_buttons.setCheckState(Qt.Checked)
        else:
            self.cb_buttons.setCheckState(Qt.Unchecked)
        return
