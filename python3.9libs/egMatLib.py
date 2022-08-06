import os
import hou
import time
import json
import uuid
import shutil
import datetime
import sys
import subprocess


# PySide2
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2 import QtUiTools


#Load This HDAs for creation
HDA_REDSHIFT = "thumbnail_Redshift::2.0"
HDA_MANTRA = "thumbnail_Mantra::2.0"
HDA_ARNOLD = "thumbnail_Arnold::3.0"


def saveMaterial(node):
    # Call from RC-Menus in Network Pane
    # Initialize
    pref = prefs()
    path = pref.get_dir() + "/"
    path = path.replace("\\", "/")

    # Save new Data to Library
    library = eg_library()
    library.load(path, pref)
    get_material_info_user(library, node)
    library.save()

    ### Update Widget
    for pane_tab in hou.ui.paneTabs():
        if pane_tab.type() == hou.paneTabType.PythonPanel:
            if pane_tab.label() == "MatLib":
                egMatLibPanel = pane_tab.activeInterfaceRootWidget()
                egMatLibPanel.update_external()
                return
    return


# Call from RC-Menus in Network Pane - Get User Info
def get_material_info_user(library, sel):
    # Get Stuff from User
    dialog = materialDialog()
    dialog.exec_()

    if dialog.canceled:
        return
    if dialog.categories:
        library.check_add_category(dialog.categories)
    if dialog.tags:
        library.check_add_tags(dialog.tags)

    library.add_material(sel, dialog.categories, dialog.tags, dialog.fav)
    return


###################################
######### THE PYTHON PANEL ########
###################################

class egMatLibPanel(QWidget):
    def __init__(self):
        super(egMatLibPanel, self).__init__()

        # Initialize
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self.prefs = prefs()
        path = self.prefs.get_dir() + "/"
        if not os.path.exists(path):
            valid = 0
            while not valid:
                path = hou.ui.selectFile(file_type=hou.fileType.Directory)
                path = hou.expandString(path)
                if os.path.exists(path):
                    valid = 1
                    self.prefs.set_dir(path)
                    self.prefs.save()
                else:
                    hou.ui.displayMessage("Please choose a valid path")
        path = path.replace("\\", "/")

        if not os.path.exists(path+"/library.json"):
            oldpath = hou.getenv("EGMATLIB")+"/def/library.json"
            shutil.copy(oldpath, path+"/library.json")
        if not os.path.exists(path+self.prefs.get_mat_dir()):
            os.mkdir(path+self.prefs.get_mat_dir())
        if not os.path.exists(path+self.prefs.get_img_dir()):
            os.mkdir(path+self.prefs.get_img_dir())

        self.path = path
        # Create Library
        self.library = eg_library()
        self.library.load(path, self.prefs)

        self.selected_cat = None
        self.filter = ""
        self.draw_mats = self.library.get_materials() # Filtererd Materials for Views

        self.active_row = None
        self.lastSelectedItems = None

        self.createView()
        self.update_views()

    def update_external(self):
        self.library.load(self.path, self.prefs)
        self.update_views()
        return

    def update_views(self):
        self.update_thumb_view()
        self.update_cat_view()
        return

    def toggle_catView(self, state): #THIS
        self.cat_layout = self.ui.findChild(QVBoxLayout, "cat_layout")
        if state == Qt.Checked:
            #self.cat_layout.setVisible(True)
            self.cat_list.setVisible(True)
            self.btn_rmv_cat.setVisible(True)
            self.btn_add_cat.setVisible(True)
        else:
            self.cat_list.setVisible(False)
            self.btn_rmv_cat.setVisible(False)
            self.btn_add_cat.setVisible(False)

        return

    ###################################
    ########### VIEW STUFF ############
    ###################################

    def createView(self):
        '''Creates the panel-view on load'''
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

        self.action_check_integrity = self.ui.findChild(QAction, 'action_check_integrity')
        self.action_check_integrity.triggered.connect(self.check_integrity)
        self.action_cleanup_db = self.ui.findChild(QAction, 'action_cleanup_db')
        self.action_cleanup_db.triggered.connect(self.cleanup_db)
        self.action_open_folder = self.ui.findChild(QAction, 'action_open_folder')
        self.action_open_folder.triggered.connect(self.open_matlib_folder)




        self.action_about = self.ui.findChild(QAction, "action_about")
        self.action_about.triggered.connect(self.show_about)

        # Link Buttons
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

        self.thumblist.setContentsMargins(0, 0, 0, 0)
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
        self.details.cellDoubleClicked.connect(self.update_entered)
        self.details.cellChanged.connect(self.changed)
        self.details.cellClicked.connect(self.cb_changed)

        # Options
        self.cb_FavsOnly = self.ui.findChild(QCheckBox, "cb_FavsOnly")
        self.cb_Redshift = self.ui.findChild(QRadioButton, "cb_Redshift")
        self.cb_Mantra = self.ui.findChild(QRadioButton, "cb_Mantra")
        self.cb_Arnold = self.ui.findChild(QRadioButton, "cb_Arnold")

        self.cb_showCat = self.ui.findChild(QCheckBox, "cb_showCat")

        self.cb_FavsOnly.stateChanged.connect(self.update_views)
        self.cb_Redshift.toggled.connect(self.update_views)
        self.cb_Mantra.toggled.connect(self.update_views)
        self.cb_Arnold.toggled.connect(self.update_views)

        self.cb_showCat.stateChanged.connect(self.toggle_catView)

        self.cb_context = self.ui.findChild(QCheckBox, "cb_context")
        self.cb_context.stateChanged.connect(self.update_context)

        # IconSize Slider
        self.slide_iconSize = self.ui.findChild(QSlider, "slide_iconSize")
        self.slide_iconSize.sliderReleased.connect(self.slide)

        # RC Menus
        self.thumblist.customContextMenuRequested.connect(self.thumblist_rc_menu)
        self.cat_list.customContextMenuRequested.connect(self.catlist_rc_menu)

        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainLayout)

    # Set IconSize via Slider
    def slide(self):
        self.library.set_thumbSize(self.slide_iconSize.value())
        #Update Thumblist Grid
        self.thumblist.setIconSize(QSize(self.library.get_thumbSize(), self.library.get_thumbSize()))
        self.thumblist.setGridSize(QSize(self.library.get_thumbSize()+10, self.library.get_thumbSize()+40))

        self.update_views()
        return

    def update_context(self, state):
        if state == Qt.Checked:
            self.library.currContext = 1
        else:
            self.library.currContext = 0
        return


    ###################################
    ############ RC MENUS #############
    ###################################

    def thumblist_rc_menu(self):
        cmenu = QMenu(self)

        importAct = cmenu.addAction("Import to Scene")
        toggleFav = cmenu.addAction("Toggle Favorite")
        renderAct = cmenu.addAction("Rerender Thumbnail")
        renderAllAct = cmenu.addAction("Render All Thumbnails")
        cmenu.addSeparator()
        delAct = cmenu.addAction("Delete Entry")
        action = cmenu.exec_(QCursor.pos())

        if action == delAct:
            self.delete_material()
        elif action == renderAct:
            self.update_single_material()
        elif action == importAct:
            self.import_materials()
        elif action == renderAllAct:
            self.update_all_materials()
        elif action == toggleFav:
            self.toggle_fav()
        return

    def toggle_fav(self):
        items = self.get_selected_items_from_thumblist()
        for item in items:
            id = self.get_id_from_thumblist(item)
            index = self.thumblist.indexFromItem(item)

            if self.library.get_material_fav(id):
                self.library.set_material_fav(id, 0)
            else:
                self.library.set_material_fav(id, 1)

        self.update_details_view(item)
        self.update_views()
        return

    def catlist_rc_menu(self):
        cmenu = QMenu(self)

        removeAct = cmenu.addAction("Remove Category")
        renameAct = cmenu.addAction("Rename Entry")
        addAct = cmenu.addAction("Add Category")
        action = cmenu.exec_(QCursor.pos())

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

    def show_about(self):

        about = AboutDialog()
        about.exec_()

        return

    def show_prefs(self):

        prefs = PrefsDialog(self.library, self.prefs)
        prefs.exec_()

        if prefs.canceled:
            return

        #Update Thumblist Grid
        self.thumblist.setIconSize(QSize(self.library.get_thumbSize(), self.library.get_thumbSize()))
        self.thumblist.setGridSize(QSize(self.library.get_thumbSize()+10, self.library.get_thumbSize()+40))
        self.update_views()
        return

    # Remove image thumbs and .mat-files not used in material library.
    def cleanup_db(self):

        materials = self.library.get_materials()
        img_path = os.path.join(self.path, self.prefs.get_img_dir())
        mat_path = os.path.join(self.path, self.prefs.get_mat_dir())

        img_thumbs = os.listdir(img_path)
        mat_files = os.listdir(mat_path)


        for img in img_thumbs:
            id = img.split(".")[0]
            found = False
            for mat in materials:
                if mat["id"] == int(id):
                    found = True
                    break
            if not found:
                try:
                    os.remove( os.path.join(img_path, img) )
                    print("File: " + os.path.join(img_path, img) + " removed")
                except:
                    pass

        for m in mat_files:
            id = m.split(".")[0]
            found = False
            for mat in materials:
                if mat["id"] == int(id):
                    found = True
                    break
            if not found:
                try:
                    os.remove( os.path.join(mat_path, m) )
                    print("File: " + os.path.join(mat_path, m) + " removed")
                except:
                    pass

        return

    # Check Integrity Of all material. Check if <id>.mat and <id>.png files are exists. If not exist - remove material from library.
    def check_integrity(self):

        materials = self.library.get_materials()

        for mat in materials:
            if mat['id'] > 0:
                img_path = os.path.join(self.path, self.prefs.get_img_dir(), "{}".format(mat['id']) + self.prefs.get_img_ext())
                mat_path = os.path.join(self.path, self.prefs.get_mat_dir(), "{}".format(mat['id']) + self.prefs.get_ext())
                #interface_path = os.path.join(self.path, self.prefs.get_mat_dir(), "{}".format(mat['id']) + ".interface")

                # Only check for img and mat for backwards compatibility
                if os.path.exists(img_path) and os.path.exists(mat_path):
                    # All clear - do nothing
                    pass
                else:
                    print("Material " +  mat['name'] + " is broken.")
                    self.library.remove_material(mat['id'])
                    self.update_thumb_view()
        return


    def open_matlib_folder(self):

        lib_dir = self.path
        lib_dir.encode("unicode_escape")


        if sys.platform != "linux" and sys.platform != "linux2":
            os.startfile(lib_dir)
            return
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, lib_dir])

        return

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
        '''Removes a category - called by user change in UI'''
        rmv_item = self.cat_list.selectedItems()
        # Prevent Deletion of "All" - Category
        if rmv_item[0].text() == "All":
            return

        self.library.remove_category(rmv_item[0].text())

        self.library.save()
        self.update_views()
        return


    def rename_category_user(self):
        '''Renames a category - called by user change in UI'''
        choice, cat = hou.ui.readInput("Please enter the new category name:")
        if choice: # Return if no
            return

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
        '''Get Filter from user and trigger view update'''
        self.filter = self.line_filter.text()
        self.update_thumb_view()
        return

    def listen_entry_from_detail(self, item):
        '''Set Detail view to Edit Mode'''
        self.active = True
        self.active_item = item
        return

    def update_entered(self, row, column):
        '''Register change in Detail view '''
        self.active_row = row

    def changed(self, row, column):
        '''Apply change in Detail view to Library '''
        if self.active_row == row:
            detail_item = self.details.item(row, column)

            items = self.lastSelectedItems
            for item in items:
                id = self.get_id_from_thumblist(item)
                if row == 0:
                    # Change Name
                    self.library.set_material_name(id, detail_item.text())
                elif row == 1:
                    # Make sure there is only one Cat per Mat
                    txt = detail_item.text()
                    pos = txt.find(",")
                    if pos != -1:
                        txt = txt[-pos]
                    self.library.set_material_cat(id, txt)
                elif row == 2:
                    self.library.set_material_tag(id, detail_item.text())
            self.library.save()
            self.update_views()

        self.active_row = None
        return

    def cb_changed(self, row, column):
        '''Apply change in Detail View - Favorite'''
        if row == 3:
            detail_item = self.details.item(row, column)
            items = self.lastSelectedItems
            for item in items:
                id = self.get_id_from_thumblist(item)
                if detail_item.checkState() is Qt.Checked:
                    self.library.set_material_fav(id, 1)
                else:
                    self.library.set_material_fav(id, 0)
            self.library.save()
            self.update_views()



    ###################################
    ########## UPDATE VIEWS ###########
    ###################################

    # Update Details view
    def update_details_view(self, item):
        '''Update upon changes in Detail view '''
        if item is None:
            return

        items = self.get_selected_items_from_thumblist_silent()

        cat_flag = False
        tag_flag = False
        if items is not None:
            #Check all Selected Mats for same Cat and Tag Values
            for x, item in enumerate(items):
                id = self.get_id_from_thumblist(item)
                curr_mat = self.library.get_material_by_id(id)

                if x == 0:
                    cat = curr_mat["categories"]
                    tags = curr_mat["tags"]
                    fav = curr_mat["favorite"]
                else:
                    #Check Categories
                    if cat != curr_mat["categories"]:
                        cat_flag = True
                    #Check Tags
                    if tags != curr_mat["tags"]:
                        tag_flag = True

        id = self.get_id_from_thumblist(item)

        for mat in self.library.get_materials():
            if mat["id"] == id:
                # set name
                table_item = self.details.item(0, 1)
                table_item.setText(mat["name"])
                # set cat
                table_item = self.details.item(1, 1)
                if cat_flag:
                    table_item.setText("Multiple Values")
                else:
                    table_item.setText(", ".join(mat["categories"]))
                # set tag
                table_item = self.details.item(2, 1)
                if tag_flag:
                    table_item.setText("Multiple Values")
                else:
                    table_item.setText(", ".join(mat["tags"]))
                # set fav
                table_item = self.details.item(3, 1)
                if mat["favorite"] == 1:
                    table_item.setCheckState(Qt.Checked)
                else:
                    table_item.setCheckState(Qt.Unchecked)
                # set id
                table_item = self.details.item(4, 1)
                table_item.setText(str(mat["id"]))
                # set Renderer
                table_item = self.details.item(5, 1)
                table_item.setText(mat["renderer"])
                # set Date
                table_item = self.details.item(6, 1)
                try:
                    table_item.setText(mat["date"])
                except:
                    table_item.setText("Not saved yet")

        #Resize
        self.details.resizeColumnToContents(1)
        if self.details.columnWidth(1) < 200:
            self.details.setColumnWidth(1,200)
        return

    # Update the Views when selection changes
    def update_selected_cat(self):
        '''Update thumb view on change of category '''
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
        '''Update cat view '''
        self.cat_list.clear()
        for cat in self.library.get_categories():
            item = QListWidgetItem(cat)
            self.cat_list.addItem(item)

        begin = self.cat_list.findItems("All", Qt.MatchExactly)[0]

        if sys.platform == "linux" or sys.platform == "linux2":
            begin.setText("000_All")
        else:
            begin.setText("___All")
        self.cat_list.sortItems()
        begin.setText("All")
        self.thumblist.sortItems()

        return

    # Filter Materials in Thumblist for Category
    def filter_view_category(self):
        '''Filter Thumbview for selected Category'''
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
        '''Filter Thumbview for entered characters in filter-Line'''
        # Filter Thumbnail View
        if self.filter == "":
            return
        tmp = []
        if self.filter.startswith("*"):
            # Filter for tags
            curr_filter = self.filter[1:]
            for mat in self.draw_mats:
                if curr_filter in mat["tags"]:
                    tmp.append(mat)
        else:
            for mat in self.draw_mats:
                if self.filter in mat["name"]:
                    tmp.append(mat)
        self.draw_mats = tmp
        return

    # Update Thumbnail View
    def update_thumb_view(self):
        '''Redraw the ThumbView with filters'''
        # Cleanup UI
        self.thumblist.clear()

        self.filter_view_category()  # Filter View by Category
        self.filter_view_filter()  # Filter View by Line Filter

        if self.draw_mats:
            for mat in self.draw_mats:
                # Pass Empty Default Material
                if mat["id"] == -1:
                    continue
                # Show only Favs
                if self.cb_FavsOnly.checkState() is Qt.Checked:
                    if mat["favorite"] == 0:
                        continue
                if self.cb_Redshift.isChecked():
                    if mat["renderer"] != "Redshift":
                        continue
                elif self.cb_Mantra.isChecked():
                    if mat["renderer"] != "Mantra":
                        continue
                elif self.cb_Arnold.isChecked():
                    if mat["renderer"] != "Arnold":
                        continue

                img = self.library.get_path() + self.prefs.get_img_dir() + str(mat["id"]) + self.prefs.get_img_ext()

                favicon = hou.getenv("EGMATLIB") + "/def/Favorite.png"
                # Check if Thumb Exists and attach
                icon = None
                if os.path.isfile(img):
                    # Draw Star Icon on Top if Favorite
                    if mat["favorite"]:
                        pm = QPixmap(self.library.get_thumbSize(), self.library.get_thumbSize())
                        pm1 = QPixmap.fromImage(QImage(img)).scaled(self.library.get_thumbSize(), self.library.get_thumbSize(), aspectMode=Qt.KeepAspectRatio)
                        pm2 = QPixmap.fromImage(QImage(favicon)).scaled(self.library.get_thumbSize(), self.library.get_thumbSize(), aspectMode=Qt.KeepAspectRatio)
                        painter = QPainter(pm)
                        painter.drawPixmap(0, 0, self.library.get_thumbSize(), self.library.get_thumbSize(), pm1)
                        painter.drawPixmap(0, 0, self.library.get_thumbSize(), self.library.get_thumbSize(), pm2)
                        painter.end()
                        icon = QIcon(pm)

                    else:
                        pixmap = QPixmap.fromImage(QImage(img)).scaled(self.library.get_thumbSize(), self.library.get_thumbSize(), aspectMode=Qt.KeepAspectRatio)
                        icon = QIcon(pixmap)
                else:
                    icon = self.default_icon()

                # Create entry in Thumblist
                #img_name = self.get_material_by_id(mat["id"])
                item = QListWidgetItem(icon, mat["name"])

                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
                item.setData(Qt.UserRole, mat["id"])  # Store ID with Thumb
                self.thumblist.addItem(item)
                self.thumblist.sortItems()


    # Create PlaceHolder Icon in case something goes wrong
    def default_icon(self):
        '''Creates the default icon if something goes wrong'''
        #Generate Default Icon
        default_img = QImage(self.library.get_thumbSize(), self.library.get_thumbSize(), QImage.Format_RGB16)
        default_img.fill(QColor(0, 0, 0))
        pixmap = QPixmap.fromImage(default_img).scaled(self.library.get_thumbSize(), self.library.get_thumbSize(), aspectMode=Qt.KeepAspectRatio)
        default_icon = QIcon(pixmap)
        return default_icon


    ###################################
    ######### LIBRARY STUFF ###########
    ###################################


    # Rerender All Visible Materials
    def update_all_materials(self):
        '''Rerenders all materials in the library - The UI is blocked for the duration of the render'''
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
        '''Rerenders a single materials in the library - The UI is blocked for the duration of the render'''
        items = self.get_selected_items_from_thumblist()
        call = False
        for item in items:
            if not item:
                return
            builder = self.import_material(item)
            id = self.get_id_from_thumblist(item)
            call = self.library.save_node(builder, id)
            builder.destroy()

        self.update_thumb_view()
        if call:
            hou.ui.displayMessage("Thumbnail(s) updated")
        return


    def get_id_from_thumblist(self, item):
        '''Return the id for the selected item in thumbview'''
        return item.data(Qt.UserRole)


    # Delete Material from Library
    def delete_material(self):
        '''Deletes the selected Material from Disk and Library'''
        if not hou.ui.displayConfirmation('This will delete the selected Material from Disk. Are you sure?'):
            return

        items = self.get_selected_items_from_thumblist()

        for item in items:
            if not item:
                return

            id = self.get_id_from_thumblist(item)
            self.library.remove_material(id)

        # Update View
        self.update_thumb_view()
        return

    # Get the selected Material from Library
    def get_selected_item_from_thumblist(self):
        '''Return the material for the selected item in thumbview'''
        item = self.thumblist.selectedItems()[0]
        if not item:
            hou.ui.displayMessage("No Material selected")
            return None
        return item

    def get_selected_items_from_thumblist(self):
        '''Return the material for the selected item in thumbview'''
        items = self.thumblist.selectedItems()
        if not items:
            hou.ui.displayMessage("No Material selected")
            return None
        self.lastSelectedItems = items
        return items

    def get_selected_items_from_thumblist_silent(self):
        '''Return the material for the selected item in thumbview'''
        items = self.thumblist.selectedItems()
        if not items:
            return None
        self.lastSelectedItems = items
        return items

    #  Saves a Material to the Library
    def save_material(self):
        '''Saves the selected nodes (Network Editor) to the Library'''
        # Get Selected from Network View
        sel = hou.selectedNodes()
        # Check selection
        if not sel:
            hou.ui.displayMessage('No Material selected')
            return
        self.get_material_info_user(sel)
        return

    def get_material_info_user(self, sel):
        '''Query user for input upon material-save'''
        # Get Stuff from User
        dialog = materialDialog()
        dialog.exec_()

        if dialog.canceled:
            return

        # Check if Category or Tags already exist
        if dialog.categories:
            self.library.check_add_category(dialog.categories)
        if dialog.tags:
            self.library.check_add_tags(dialog.tags)

        for mat in sel:
            self.library.add_material(mat, dialog.categories, dialog.tags, dialog.fav)
        self.update_views()

        return


    def import_materials(self):
        items = self.get_selected_items_from_thumblist()
        for item in items:
            self.import_material(item)
        #hou.ui.displayMessage("Materials imported")
        return

    #  Import Material to Scene
    def import_material(self, sel=None):
        '''Import Material to scene'''
        if not sel:
            item = self.thumblist.selectedItems()[0]
        else:
            item = sel

        if not item:
            hou.ui.displayMessage("No Material selected")
            return

        id = self.get_id_from_thumblist(item)
        return self.library.import_material(id)



###################################
########### THE LIBRARY ###########
###################################

class eg_library():
    def __init__(self):
        self.materials = None
        self.categories = None
        self.tags = None
        self.settings = None
        self.path = None
        self.currContext = 0

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


    def set_material_name(self, id, name):
        '''Sets the Name for the given Material (id)'''
        mat = self.get_material_by_id(id)
        mat["name"] = name


    def get_material_by_id(self, id):
        '''Returns the Library-Entry for the given id'''
        for mat in self.materials:
            if int(id) == mat["id"]:
                return mat
        return None


    def set_material_cat(self, id, cat):
        '''Sets the category for the given Material (id)'''
        self.check_add_category(cat)
        mat = self.get_material_by_id(id)

        cats = cat.split(",")
        for c in cats:
            c = c.replace(" ", "")
        mat["categories"] = cats
        return


    def set_material_tag(self, id, tag):
        '''Sets the tag for the given Material (id)'''
        mat = self.get_material_by_id(id)
        tags = tag.split(",")
        for t in tags:
            t = t.replace(" ", "")
        mat["tags"] = tags
        return


    def set_material_fav(self, id, fav):
        '''Sets the fav for the given Material (id)'''
        mat = self.get_material_by_id(id)
        mat["favorite"] = fav


    def get_material_fav(self, id):
        '''Gets the fav for the given Material (id) as 0/1'''
        mat = self.get_material_by_id(id)
        return mat["favorite"]


    def remove_material(self, id):
        '''Removes a Material from this Library and Disk'''
        for mat in self.materials:
            if id == mat["id"]:
                self.materials.remove(mat)

                #Remove Files from Disk
                mat_file_path = os.path.join( self.path , self.settings.get_mat_dir(), str(id) + self.settings.get_ext() )
                img_file_path = os.path.join( self.path , self.settings.get_img_dir(), str(id) + self.settings.get_img_ext() )
                interface_file_path = os.path.join( self.path , self.settings.get_mat_dir(), str(id) + ".interface" )

                if os.path.exists(mat_file_path):
                    os.remove(mat_file_path)
                if os.path.exists(img_file_path):
                    os.remove(img_file_path)
                if os.path.exists(interface_file_path):
                    os.remove(interface_file_path)

                self.save()
                return

    def check_add_category(self, cat):
        '''Checks if this category exists and adds it if needed'''
        cats = cat.split(",")
        for c in cats:
            c = c.replace(" ", "")
            if c != "":
                if c not in self.categories:
                    self.categories.append(c)
        return

    def check_add_tags(self, tags):
        '''Checks if this tag exists and adds it if needed'''
        tags = tags.split(",")
        for t in tags:
            t = t.replace(" ", "")
            if t != "":
                if t not in self.tags:
                    self.tags.append(t)
        return

    def add_material(self, node, cats, tags, fav):
        '''Add a Material to this Library'''
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

            renderer = ""
            if node.type().name() == "redshift_vopnet":
                renderer = "Redshift"
                builder = 1
            elif node.type().name() == "materialbuilder":
                renderer = "Mantra"
                builder = 1
            elif node.type().name() == "principledshader::2.0":
                renderer = "Mantra"
                builder = 0
            elif node.type().name() == "arnold_materialbuilder":
                renderer = "Arnold"
                builder = 1


            date = str(datetime.datetime.now())
            date = date[:-7]

            material = {"id": id, "name": name, "categories": cats, "tags": tags, "favorite": fav, "renderer": renderer, "date": date, "builder": builder}
            self.materials.append(material)
            self.save()
        return

    def get_renderer_by_id(self, id):
        '''Return the Renderer for this Material as a string'''
        for mat in self.materials:
            if int(id) == mat["id"]:
                return mat["renderer"]
        return None

    def check_materialBuilder_by_id(self, id):
        '''Return if the Material is a Builder (Mantra) as a 0/1'''
        for mat in self.materials:
            if int(id) == mat["id"]:
                return mat["builder"]
        return None

    def get_current_network_node(self):
        '''Return thre current Node in the Network Editor'''
        for pt in hou.ui.paneTabs():
            if pt.type() == hou.paneTabType.NetworkEditor:
                return pt.currentNode()
        return None

    def remove_category(self, cat):
        '''Removes the given category from the library (and also in all Materials)'''
        self.categories.remove(cat)
        # check materials against category and remove there also:
        for mat in self.materials:
            if cat in mat["categories"]:
                mat["categories"].remove(cat)
        return

    def rename_category(self, old, new):
        '''Renames the given category in the library (and also in all Materials)'''
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

    def import_material(self, id):
        '''Import a Material to the Nework Editor/Scene'''
        file_name = self.get_path() + self.settings.get_mat_dir() + str(id) + self.settings.get_ext()

        mat = self.get_material_by_id(id)

        renderer = self.get_renderer_by_id(id)
        builder = None

        # Import to current context
        import_path = ('/mat')
        if self.currContext:
            currNode = self.get_current_network_node()
            if currNode is None:
                import_path = ('/mat')

            # if current node is VOP node like "redshift_vopnet" try to go level up in hierarchy and stop when path equal to "/mat" or parent type = "matnet"
            elif isinstance(currNode, hou.VopNode):
                while (currNode.path() != '/mat' and currNode.type().name() != 'matnet') :
                    currNode = currNode.parent()

            if currNode.type().name() != "matnet" and currNode.path() != "/mat":
                matnet = hou.node(currNode.path()).createNode("matnet")
                # Use existing Matnet if available
                for n in currNode.children():
                    if n.type().name() != "matnet":
                        matnet = n
                        break
                import_path = matnet.path()
            else:
                import_path = currNode.path()

        parms_file_name = self.get_path() + self.settings.get_mat_dir() + str(id) + ".interface"


        #Create temporary storage of nodes
        tmp_matnet = hou.node("obj").createNode("matnet")
        hou_parent = tmp_matnet # needed for the code script below


        if renderer == "Redshift":
            #Interface Check
            if os.path.exists(parms_file_name):
                interface_file = open(parms_file_name, 'r')
                code = interface_file.read()
                exec(code)

                builder = hou_parent.children()[0]

            else:
                builder = hou.node(import_path).createNode('redshift_vopnet')

            builder.setName(mat["name"], unique_name=True)
            # Delete Default children in RS-VopNet
            for node in builder.children():
                    node.destroy()


        elif renderer == "Mantra":
            #Interface Check
            if os.path.exists(parms_file_name):
                # Only load parms if MatBuilder
                if self.check_materialBuilder_by_id(id):
                    interface_file = open(parms_file_name, 'r')
                    code = interface_file.read()
                    exec(code)

                    builder = hou.selectedNodes()[0]
                # Selection will be empty if not a MaterialBuilder
                else:
                    builder = hou.node(import_path).createNode('materialbuilder')
            else:
                builder = hou.node(import_path).createNode('materialbuilder')

            builder.setName(mat["name"], unique_name=True)
            # Delete Default children in MaterialBuilder
            for node in builder.children():
                node.destroy()


        elif renderer == "Arnold":
            # CreateBuilder
            #Interface Check
            if os.path.exists(parms_file_name):
                interface_file = open(parms_file_name, 'r')
                code = interface_file.read()
                exec(code)

                builder = hou_parent.children()[0]
            else:
                builder = hou.node(import_path).createNode('arnold_materialbuilder')

            builder.setName(mat["name"], unique_name=True)
            # Delete Default children in Arnold MaterialBuilder
            for node in builder.children():
                    node.destroy()


        # Import file from disk
        try:
            builder.loadItemsFromFile(file_name, ignore_load_warnings=False)
        except:
            hou.ui.displayMessage("File not found on Disk")
            return

        # If node is Principled Shader
        if renderer == "Mantra" and not self.check_materialBuilder_by_id(id):
            n = builder.children()[0]
            hou.moveNodesTo((n, ), builder.parent())
            builder.destroy()
            builder = hou.selectedNodes()[0]

        else:
            new_mat = hou.moveNodesTo((builder,), hou.node(import_path) )
            new_mat[0].moveToGoodPosition()
            builder = new_mat[0]

        #Cleanup
        tmp_matnet.destroy()

        return builder


    def save_node(self, node, id):
        '''Save Node wrapper for different Material Types'''
        # Check against NodeType
        val = False
        if node.type().name() == "redshift_vopnet":
            #Interruptable
            with hou.InterruptableOperation("Rendering", "Performing Tasks", open_interrupt_dialog=True) as operation:
                val= self.save_node_redshift(node, id)
        elif node.type().name() == "materialbuilder" or node.type().name() == "principledshader::2.0":
            #Interruptable
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")
                return False
            with hou.InterruptableOperation("Rendering", "Performing Tasks", open_interrupt_dialog=True) as operation:
                val = self.save_node_mantra(node, id)
        elif node.type().name() == "arnold_materialbuilder":
            if hou.getenv("OCIO") is None:
                hou.ui.displayMessage("Please set $OCIO first")
                return False
            with hou.InterruptableOperation("Rendering", "Performing Tasks", open_interrupt_dialog=True) as operation:
                val = self.save_node_arnold(node, id)
        else:
            hou.ui.displayMessage('Selected Node is not a Material Builder')
        return val


    def save_node_redshift(self, node, id):
        '''Saves the Redshift node to disk - does not add to library'''
        # Filepath where to save stuff
        file_name = self.get_path() + self.settings.get_mat_dir() + str(id) + self.settings.get_ext()

        #interface-stuff
        parms_file_name = self.get_path() + self.settings.get_mat_dir() + str(id) + ".interface"
        children = node.children()

        interface_file = open(parms_file_name, 'w')
        #interface_file.write(node.parmTemplateGroup().asCode())
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # Create Thumbnail
        thumb = hou.node("/obj").createNode(HDA_REDSHIFT)
        thumb.parm("mat").set(node.path())

        # Build path
        path = self.get_path()  + self.settings.get_img_dir() + str(id) + self.settings.get_img_ext()

        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path)
        exclude = "* ^" + thumb.name()
        thumb.parm("obj_exclude").set(exclude)
        lights = thumb.name() + "/*"
        thumb.parm("lights").set(lights)
        thumb.parm("resx").set(self.rendersize)
        thumb.parm("resy").set(self.rendersize)

        # Render Frame
        thumb.parm("execute").pressButton()
        # CleanUp
        thumb.destroy()
        return True

    def save_node_arnold(self, node, id): #ARNOLD
        '''Saves the Arnold node to disk - does not add to library'''
        # Filepath where to save stuff
        file_name = self.get_path() + self.settings.get_mat_dir() + str(id) + self.settings.get_ext()

        #interface-stuff
        parms_file_name = self.get_path() + self.settings.get_mat_dir() + str(id) + ".interface"
        children = node.children()

        interface_file = open(parms_file_name, 'w')
        #interface_file.write(node.parmTemplateGroup().asCode())
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # children = node.children()
        # node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        # Create Thumbnail
        thumb = hou.node("/obj").createNode(HDA_ARNOLD)
        thumb.parm("mat").set(node.path())

        # Build path
        path = self.get_path()  + self.settings.get_img_dir() + str(id)

        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path+".exr")
        thumb.parm("cop_out_img").set(path+self.settings.get_img_ext())

        exclude = "* ^" + thumb.name()
        thumb.parm("obj_exclude").set(exclude)
        lights = thumb.name() + "/*"
        thumb.parm("lights").set(lights)
        thumb.parm("resx").set(self.rendersize)
        thumb.parm("resy").set(self.rendersize)
        thumb.parm("ar_light_color_texture").set(hou.getenv("EGMATLIB")+"/img/photo_studio_01_4k_ACEScg.hdr")

        # Render Frame
        thumb.parm("render").pressButton()

        #WaitForRender - A really bad hack

        done_path = hou.getenv("EGMATLIB")+"/lib/done.txt"
        mustend = time.time() + 60.0
        while time.time() < mustend:
            if os.path.exists(done_path):
                os.remove(done_path)
                time.sleep(2)
                break
            time.sleep(1)


        thumb.destroy()
        if os.path.exists(path+".exr"):
            os.remove(path+".exr")

        return True

    def save_node_mantra(self, node, id):
        '''Saves the Mantra node to disk - does not add to library'''
        # Filepath where to save stuff
        file_name = self.get_path() + self.settings.get_mat_dir() + str(id) + self.settings.get_ext()

        origNode = node
        builder = ""
        if node.type().name() != "materialbuilder":
            builder = hou.node("/mat").createNode("materialbuilder")
            for c in builder.children():
                c.destroy()
            hou.copyNodesTo((node,), builder)
            node = builder

         #interface-stuff
        parms_file_name = self.get_path() + self.settings.get_mat_dir() + str(id) + ".interface"
        children = node.children()

        interface_file = open(parms_file_name, 'w')
        #interface_file.write(node.parmTemplateGroup().asCode())
        interface_file.write(node.asCode())

        node.saveItemsToFile(children, file_name, save_hda_fallbacks=False)

        node = origNode
        if builder != "":
            builder.destroy()

        # Create Thumbnail
        thumb = hou.node("/obj").createNode(HDA_MANTRA)
        thumb.parm("mat").set(node.path())

        # Build path
        path = self.get_path() + self.settings.get_img_dir() + str(id)

        #  Set Rendersettings and Object Exclusions for Thumbnail Rendering
        thumb.parm("path").set(path+".exr")
        thumb.parm("cop_out_img").set(path+self.settings.get_img_ext())
        exclude = "* ^" + thumb.name()
        thumb.parm("obj_exclude").set(exclude)
        lights = thumb.name() + "/*"
        thumb.parm("lights").set(lights)
        thumb.parm("resx").set(self.rendersize)
        thumb.parm("resy").set(self.rendersize)

        # Render Frame
        thumb.parm("render").pressButton()


        # CleanUp
        thumb.destroy()
        if os.path.exists(path+".exr"):
            os.remove(path+".exr")

        return True



###################################
########  THE USER PREFS ##########
###################################
class prefs():
    def __init__(self):
        self.path = hou.getenv("EGMATLIB")
        self.data = {}
        self.load()

    def save(self):
        self.data["directory"] = self.directory
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


###################################
######  THE MATERIAL DIALOG  ######
###################################
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

    # Confirm Material Creation
    def confirm(self):
        self.categories = self.line_cats.text()
        self.tags = self.line_tags.text()
        self.fav = self.cb_fav.isChecked()
        self.accept()

    # Cancel Material Creation
    def destroy(self):
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
        file = QFile(self.script_path + '/Prefs.ui')
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # UI
        self.line_workdir = self.ui.findChild(QLineEdit, 'line_workdir')
        self.line_thumbsize = self.ui.findChild(QLineEdit, 'line_thumbsize')
        self.line_rendersize = self.ui.findChild(QLineEdit, 'line_rendersize')

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

        self.line_workdir.setText(self.directory)
        self.line_rendersize.setText(str(self.rendersize))
        self.line_thumbsize.setText(str(self.thumbsize))


class AboutDialog(QDialog):
    def __init__(self):
        super(AboutDialog, self).__init__()
        self.script_path = os.path.dirname(os.path.realpath(__file__))

        ## LOAD UI
        ## Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QFile(self.script_path + '/About.ui')
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainLayout)
