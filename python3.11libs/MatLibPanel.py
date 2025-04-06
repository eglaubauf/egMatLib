import os
from re import S

import hou
import shutil
import sys
import subprocess

import importlib
import MatLibCore
import MatLibDialogs
import MatLibPrefs

# TODO: FUTURE
# import egx_matTools.egx_matPerFolder.folderProcessor as importMat
# from egx_matTools.egx_materialBuild_MatX import controller as importMatX
# from egx_matTools.egx_materialBuild_Mantra import controller as importMantra

importlib.reload(MatLibCore)
importlib.reload(MatLibPrefs)

# TODO: FUTURE
# importlib.reload(importMat)
# importlib.reload(importMatX)
# importlib.reload(importMantra)

from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2 import QtUiTools


def saveMaterial(node):
    # Call from RC-Menus in Network Pane
    # Initialize
    pref = MatLibPrefs.prefs()
    path = pref.get_dir() + "/"
    path = path.replace("\\", "/")

    # Save new Data to Library
    library = MatLibCore.MaterialLibrary()
    library.load(path, pref)

    # Get Stuff from User
    dialog = MatLibDialogs.usdDialog()
    dialog.exec_()
    if dialog.canceled:
        return
    # Check if Category or Tags already exist
    if dialog.categories:
        library.check_add_category(dialog.categories)
    if dialog.tags:
        library.check_add_tags(dialog.tags)
    for asset in hou.selectedNodes():
        library.add_asset(asset, dialog.categories, dialog.tags, dialog.fav)

    library.save()

    ### Update Widget
    for pane_tab in hou.ui.paneTabs():
        if pane_tab.type() == hou.paneTabType.PythonPanel:
            if pane_tab.label() == "MatLib":
                egMatLibPanel = pane_tab.activeInterfaceRootWidget()
                egMatLibPanel.update_external()
                return
    return


class MatLibPanel(QWidget):
    def __init__(self):
        super(MatLibPanel, self).__init__()

        # Initialize
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self.prefs = MatLibPrefs.prefs()
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

        if not os.path.exists(path + "/library.json"):
            oldpath = hou.getenv("EGMATLIB") + "/def/library.json"
            shutil.copy(oldpath, path + "/library.json")
        if not os.path.exists(path + self.prefs.get_img_dir()):
            os.mkdir(path + self.prefs.get_img_dir())
            os.mkdir(path + self.prefs.get_asset_dir())

        self.path = path
        # Create Library
        self.library = MatLibCore.MaterialLibrary()
        self.library.load(path, self.prefs)

        self.selected_cat = None
        self.filter = ""
        self.draw_assets = self.library.get_assets()  # Filterered assets for Views

        self.active_row = None
        self.lastSelectedItems = None

        self.edit = False

        self.createView()
        self.update_views()

    def update_external(self):
        self.library.load(self.path, self.prefs)
        self.update_views()
        return

    def update_views(self):
        self.update_ui()
        self.update_thumb_view()
        self.update_cat_view()
        return

    def update_ui(self):
        if self.cb_Mantra.isChecked():
            self.radio_USD.setDisabled(False)
            self.radio_current.setDisabled(False)
        if self.cb_MatX.isChecked():
            self.radio_USD.setDisabled(False)
            self.radio_current.setDisabled(False)
        if self.cb_Arnold.isChecked():
            self.radio_default.setChecked(True)
            self.radio_USD.setDisabled(True)
            self.radio_current.setDisabled(True)
        if self.cb_Redshift.isChecked():
            self.radio_default.setChecked(True)
            self.radio_USD.setDisabled(True)
            self.radio_current.setDisabled(True)
        if self.cb_Octane.isChecked():
            self.radio_default.setChecked(True)
            self.radio_USD.setDisabled(True)
            self.radio_current.setDisabled(True)

    def toggle_catView(self):
        if self.action_catView.isChecked():
            self.cat_list.setVisible(True)
            self.action_catView.setChecked(True)
        else:
            self.cat_list.setVisible(False)
            self.action_catView.setChecked(False)

    def toggle_catView_rc(self):
        if not self.action_catView.isChecked():
            self.cat_list.setVisible(True)
            self.action_catView.setChecked(True)
        else:
            self.cat_list.setVisible(False)
            self.action_catView.setChecked(False)

    def toggle_detailsView(self):
        self.details_widget = self.ui.findChild(QWidget, "details_widget")

        if self.action_detailsview.isChecked():
            self.details_widget.setHidden(False)
            self.action_detailsview.setChecked(True)
        else:
            self.details_widget.setHidden(True)
            self.action_detailsview.setChecked(False)

    def toggle_detailsView_rc(self):

        if not self.action_detailsview.isChecked():
            self.details_widget.setHidden(False)
            self.action_detailsview.setChecked(True)
        else:
            self.details_widget.setHidden(True)
            self.action_detailsview.setChecked(False)

    ###################################
    ########### VIEW STUFF ############
    ###################################

    def createView(self):
        """Creates the panel-view on load"""
        ## Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QFile(self.script_path + "/MatLib.ui")
        file.open(QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # Helper for Table_Trigger
        self.active = False

        # Load Ui Element so self
        self.menu = self.ui.findChild(QMenuBar, "menubar")
        self.menuGoto = self.ui.findChild(QMenu, "menu_file")
        self.action_prefs = self.ui.findChild(QAction, "action_prefs")
        self.action_prefs.triggered.connect(self.show_prefs)

        self.menu_view = self.ui.findChild(QMenu, "menu_view")
        self.action_catView = self.ui.findChild(QAction, "action_show_cat")
        self.action_catView.triggered.connect(self.toggle_catView)

        self.action_detailsview = self.ui.findChild(QAction, "action_show_details")
        self.action_detailsview.triggered.connect(self.toggle_detailsView)

        self.action_cleanup_db = self.ui.findChild(QAction, "action_cleanup_db")
        self.action_cleanup_db.triggered.connect(self.cleanup_db)
        self.action_open_folder = self.ui.findChild(QAction, "action_open_folder")
        self.action_open_folder.triggered.connect(self.open_usdlib_folder)

        self.action_about = self.ui.findChild(QAction, "action_about")
        self.action_about.triggered.connect(self.show_about)

        # TODO: FUTURE
        # self.action_import_folder = self.ui.findChild(QAction, "action_import_folder")
        # self.action_import_folder.triggered.connect(self.import_folder)

        self.action_import_files = self.ui.findChild(QAction, "action_import_files")
        self.action_import_files.triggered.connect(self.import_files)

        self.action_force_update = self.ui.findChild(QAction, "action_force_update")
        self.action_force_update.triggered.connect(self.update_external)

        self.thumblist = self.ui.findChild(QListWidget, "listw_matview")
        self.thumblist.setIconSize(
            QSize(self.library.get_thumbSize(), self.library.get_thumbSize())
        )
        self.thumblist.doubleClicked.connect(self.import_asset)
        self.thumblist.itemPressed.connect(self.update_details_view)
        self.thumblist.setGridSize(
            QSize(self.library.get_thumbSize() + 10, self.library.get_thumbSize() + 40)
        )
        self.thumblist.setContentsMargins(0, 0, 0, 0)
        self.thumblist.setSortingEnabled(True)

        # Category UI
        self.cat_list = self.ui.findChild(QListWidget, "listw_catview")
        self.cat_list.clicked.connect(self.update_selected_cat)

        # FILTER UI
        self.line_filter = self.ui.findChild(QLineEdit, "line_filter")
        self.line_filter.textChanged.connect(self.filter_thumb_view_user)

        # Updated Details UI
        self.details = self.ui.findChild(QTableWidget, "details_widget")
        self.line_name = self.ui.findChild(QLineEdit, "line_name")
        self.line_cat = self.ui.findChild(QLineEdit, "line_cat")
        self.line_tags = self.ui.findChild(QLineEdit, "line_tags")
        self.line_id = self.ui.findChild(QLineEdit, "line_id")
        self.line_render = self.ui.findChild(QLineEdit, "line_render")
        self.line_date = self.ui.findChild(QLineEdit, "line_date")
        self.box_fav = self.ui.findChild(QCheckBox, "cb_fav")
        self.btn_update = self.ui.findChild(QPushButton, "btn_update")
        self.btn_update.clicked.connect(self.user_update_asset)

        # Options
        self.cb_FavsOnly = self.ui.findChild(QCheckBox, "cb_FavsOnly")
        self.cb_FavsOnly.stateChanged.connect(self.update_views)

        # Material
        self.cb_Redshift = self.ui.findChild(QRadioButton, "cb_Redshift")
        self.cb_Mantra = self.ui.findChild(QRadioButton, "cb_Mantra")
        self.cb_Arnold = self.ui.findChild(QRadioButton, "cb_Arnold")
        self.cb_Octane = self.ui.findChild(QRadioButton, "cb_Octane")
        self.cb_MatX = self.ui.findChild(QRadioButton, "cb_MatX")

        self.cb_showCat = self.ui.findChild(QCheckBox, "cb_showCat")

        self.cb_FavsOnly.stateChanged.connect(self.update_views)

        self.cb_Redshift.toggled.connect(self.update_views)
        self.cb_Mantra.toggled.connect(self.update_views)
        self.cb_Arnold.toggled.connect(self.update_views)
        self.cb_Octane.toggled.connect(self.update_views)
        self.cb_MatX.toggled.connect(self.update_views)

        # Context Options
        self.radio_current = self.ui.findChild(QRadioButton, "radio_current")
        self.radio_current.toggled.connect(self.update_context)

        self.radio_USD = self.ui.findChild(QRadioButton, "radio_USD")
        self.radio_USD.toggled.connect(self.update_context)

        self.radio_default = self.ui.findChild(QRadioButton, "radio_default")
        self.radio_default.toggled.connect(self.update_context)

        # IconSize Slider
        self.slide_iconSize = self.ui.findChild(QSlider, "slide_iconSize")
        self.slide_iconSize.sliderReleased.connect(self.slide)

        # RC Menus
        self.thumblist.customContextMenuRequested.connect(self.thumblist_rc_menu)
        self.cat_list.customContextMenuRequested.connect(self.catlist_rc_menu)

        # TODO: Hide Menus for now - FUTURE
        self.a_folder = self.ui.findChild(QAction, "action_import_folder")
        self.a_folder.setDisabled(True)
        self.a_folder.setVisible(False)

        self.a_files = self.ui.findChild(QAction, "action_import_files")
        self.a_files.setDisabled(True)
        self.a_files.setVisible(False)

        self.menu_import = self.ui.findChild(QMenu, "menuImport")
        self.menu_import.setDisabled(True)

        # set main layout and attach to widget
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.ui)
        mainLayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainLayout)

        # Cleanup UI
        self.setStyleSheet("""  font-family: Lato; """)
        self.menu.setStyleSheet(""" font-family: Lato; """)
        self.menuGoto.setStyleSheet("""  font-family: Lato; """)
        self.menu_import.setStyleSheet("""  font-family: Lato; """)

    # Set IconSize via Slider
    def slide(self):
        self.library.set_thumbSize(self.slide_iconSize.value())
        # Update Thumblist Grid
        self.thumblist.setIconSize(
            QSize(self.library.get_thumbSize(), self.library.get_thumbSize())
        )
        self.thumblist.setGridSize(
            QSize(self.library.get_thumbSize() + 10, self.library.get_thumbSize() + 40)
        )

        self.update_views()
        return

    def update_context(self, state):
        if self.radio_USD.isChecked():
            self.library.set_context(hou.node("/stage"))
        elif self.radio_current.isChecked():
            self.library.set_context(self.get_current_network_node())
        elif self.radio_default.isChecked():
            self.library.set_context(hou.node("/mat"))
        return

    def get_current_network_node(self):
        """Return thre current Node in the Network Editor"""
        for pt in hou.ui.paneTabs():
            if pt.type() == hou.paneTabType.NetworkEditor:
                return pt.currentNode()
        return None

    ###################################
    ############ RC MENUS #############
    ###################################

    def thumblist_rc_menu(self):
        cmenu = QMenu(self)

        importAct = cmenu.addAction("Import to Scene")
        toggleFav = cmenu.addAction("Toggle Favorite")
        renderAct = cmenu.addAction("Rerender Thumbnail")
        renderAllAct = cmenu.addAction("Render All Thumbnails")
        thumbViewport = cmenu.addAction("Thumbnail from Viewport")
        cmenu.addSeparator()
        delAct = cmenu.addAction("Delete Entry")
        cmenu.addSeparator()
        toggle_cats = cmenu.addAction("Toggle Cat View")
        toggle_details = cmenu.addAction("Toggle Details View")
        action = cmenu.exec_(QCursor.pos())

        if action == delAct:
            self.delete_asset()
        elif action == renderAct:
            self.update_single_asset()
        elif action == importAct:
            self.import_assets()
        elif action == renderAllAct:
            self.update_all_assets()
        elif action == thumbViewport:
            self.update_single_asset(True)
        elif action == toggleFav:
            self.toggle_fav()
        elif action == toggle_details:
            self.toggle_detailsView_rc()
        elif action == toggle_cats:
            self.toggle_catView_rc()

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

    def toggle_fav(self):
        items = self.get_selected_items_from_thumblist()
        for item in items:
            id = self.get_id_from_thumblist(item)
            # index = self.thumblist.indexFromItem(item)

            if self.library.get_asset_fav(id):
                self.library.set_asset_fav(id, 0)
            else:
                self.library.set_asset_fav(id, 1)

        self.update_details_view(item)
        self.update_views()
        return

    # def import_folder(self):
    #     self.h = importMat.Controller()
    #     self.h.show()
    #     self.h.finished.connect(self.import_folder_finished)

    def import_folder_finished(self):
        ###f inalize import by adding the created materials to the library
        materials = self.h.core.get_new_materials()
        nodes = []
        for mat in materials:
            if mat.getNode().type().name() == "materiallibrary":
                nodes.append(mat.get_output())
            else:
                nodes.append(mat.getNode())
        self.get_material_info_user(nodes)

    def import_files(self):
        msg = "Choose Material type to create"
        buttons = ["Principled", "MaterialX", "Cancel"]
        choice = hou.ui.displayMessage(msg, buttons)
        if choice < 0 or choice == len(buttons) - 1:
            return
        # TODO: FUTURE
        # elif choice == 0:
        #     self.h = importMantra.Controller()
        #     self.h.show()
        #     self.h.finished.connect(self.import_files_finished)
        # else:
        #     self.h = importMatX.Controller()
        #     self.h.show()
        #     self.h.finished.connect(self.import_files_finished)

    def import_files_finished(self):
        ### finalize import by adding the created materials to the library
        mat = self.h.core.get_new_material()
        nodes = []
        if mat.getNode().type().name() == "materiallibrary":
            nodes.append(mat.get_output())
        else:
            nodes.append(mat.getNode())
        self.get_material_info_user(nodes)

    ###################################
    ########### USER STUFF ############
    ###################################

    def show_about(self):
        about = MatLibDialogs.AboutDialog()
        about.exec_()
        return

    def show_prefs(self):
        prefs = MatLibDialogs.PrefsDialog(self.library, self.prefs)
        prefs.exec_()

        if prefs.canceled:
            return

        # Update Thumblist Grid
        self.thumblist.setIconSize(
            QSize(self.library.get_thumbSize(), self.library.get_thumbSize())
        )
        self.thumblist.setGridSize(
            QSize(self.library.get_thumbSize() + 10, self.library.get_thumbSize() + 40)
        )
        self.update_views()
        return

    # Remove image thumbs and .asset-files not used in material library.
    def cleanup_files(self):
        assets = self.library.get_assets()
        img_path = os.path.join(self.path, self.prefs.get_img_dir())
        asset_path = os.path.join(self.path, self.prefs.get_asset_dir())

        img_thumbs = os.listdir(img_path)
        asset_files = os.listdir(asset_path)

        for img in img_thumbs:
            id = img.split(".")[0]
            found = False
            for asset in assets:
                if asset.get_id() == int(id):
                    found = True
                    break
            if not found:
                if asset.get_id() > 0:
                    try:
                        os.remove(os.path.join(img_path, img))
                        print("File: " + os.path.join(img_path, img) + " removed")
                        self.library.remove_asset(id)
                    except:
                        pass

        for m in asset_files:
            id = m.split(".")[0]
            if "img" in id:
                return
            found = False
            for asset in assets:
                if asset.get_id() == int(id):
                    found = True
                    break
            if not found:
                if asset.get_id() > 0:
                    try:
                        os.remove(os.path.join(asset_path, m))
                        print("File: " + os.path.join(asset_path, m) + " removed")
                        self.library.remove_asset(id)
                    except:
                        pass

        for asset in assets:
            path = asset.get_path()
            if not os.path.exists(path):
                try:
                    # os.remove(os.path.join(asset_path, m))
                    print("File: " + path + " removed")
                    self.library.remove_asset(asset.get_id())
                except:
                    pass
        self.update_thumb_view()
        return

    def cleanup_db(self):
        assets = self.library.get_assets()
        mark_rmv = 0
        mark_render = 0

        for asset in assets:
            if asset.get_id() > 0:
                interface_path = os.path.join(
                    self.path,
                    self.prefs.get_asset_dir(),
                    str(asset.get_id()) + ".interface",
                )
                mat_path = os.path.join(
                    self.path, self.prefs.get_asset_dir(), str(asset.get_id()) + ".mat"
                )
                img_path = os.path.join(
                    self.path,
                    self.prefs.get_img_dir(),
                    str(asset.get_id()) + self.prefs.get_img_ext(),
                )

                # asset_path = asset.get_path()
                if not os.path.exists(interface_path):
                    print("Asset %d missing on disk. Removing.", asset.get_id())
                    mark_rmv = 1
                    self.library.remove_asset(asset.get_id())
                if not os.path.exists(mat_path):
                    print("Asset %d missing on disk. Removing.", asset.get_id())
                    mark_rmv = 1
                    self.library.remove_asset(asset.get_id())
                if not os.path.exists(img_path):
                    mark_render = 1
                    print(
                        "Image for Asset %d missing on disk. Needs Rendering."
                        % asset.get_id()
                    )

        mats_path = os.path.join(self.path, self.prefs.get_asset_dir())
        mark_lone = 0
        for f in os.listdir(mats_path):
            if f.endswith(".mat") or f.endswith(".interface"):
                split = f.split(".")[0]
                mark_found = 0
                for a in assets:
                    if str(split) in str(a.get_id()):
                        mark_found = 1
                        break
                if not mark_found:
                    print(
                        "Lonely File at %s found. Removing from disk"
                        % os.path.join(mats_path, f)
                    )
                    os.remove(os.path.join(mats_path, f))
                    mark_lone = 1

        if mark_rmv:
            hou.ui.displayMessage(
                "Assets have been cleaned up. See python shell for details"
            )
        if mark_render:
            hou.ui.displayMessage(
                "Missing images have been found. Rerender thumbs required"
            )
        if mark_lone:
            hou.ui.displayMessage("Lone files have been found and removed from disk.")

        self.update_thumb_view()
        return

    def render_missing(self):
        assets = self.library.get_assets()

        for asset in assets:
            if asset.get_id() > 0:
                img_path = os.path.join(
                    self.path,
                    self.prefs.get_img_dir(),
                    str(asset.get_id()) + self.prefs.get_img_ext(),
                )
                # print(img_path)
                asset_path = asset.get_path()

                # Only check for img and asset for backwards compatibility
                if os.path.exists(img_path) and os.path.exists(asset_path):
                    # All clear - do nothing
                    continue
                else:
                    if not os.path.exists(img_path):
                        print("Render Thumbnail for Asset " + asset.get_name())
                        self.render_thumbnail(asset.get_id())
                    elif not os.path.exists(asset_path):
                        print("Asset missing on disk. Removing.")
                        self.library.remove_asset(asset.get_id())
                    self.update_thumb_view()
        return

    def open_usdlib_folder(self):
        lib_dir = self.path
        lib_dir.encode("unicode_escape")

        if sys.platform == "linux" and sys.platform == "linux2":  # Linux
            os.startfile(lib_dir)
            return
        elif sys.platform == "darwin":  # MacOS
            opener = "open"
            subprocess.call([opener, lib_dir])
        else:  # Windows
            os.startfile(lib_dir)

        return

    # User Adds Category with Button
    def add_category_user(self):
        choice, cat = hou.ui.readInput("Please enter the new category name:")
        if choice:  # Return if no
            return
        self.library.check_add_category(cat)
        self.library.save()
        self.update_views()
        return

    # User Removes Category with Button
    def rmv_category_user(self):
        """Removes a category - called by user change in UI"""
        rmv_item = self.cat_list.selectedItems()
        # Prevent Deletion of "All" - Category
        if rmv_item[0].text() == "All":
            return

        self.library.remove_category(rmv_item[0].text())

        self.library.save()
        self.update_views()
        return

    def rename_category_user(self):
        """Renames a category - called by user change in UI"""
        choice, cat = hou.ui.readInput("Please enter the new category name:")
        if choice:  # Return if no
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
        """Get Filter from user and trigger view update"""
        self.filter = self.line_filter.text()
        self.update_thumb_view()
        return

    def listen_entry_from_detail(self, item):
        """Set Detail view to Edit Mode"""
        self.active = True
        self.active_item = item
        return

    ###################################
    ########## UPDATE VIEWS ###########
    ###################################

    def user_update_asset(self):

        self.user_update_cats()
        self.user_update_name()
        self.user_update_tags()
        self.user_update_fav()
        self.user_update_date()
        self.update_views()

        return

    def user_update_cats(self):
        """Apply change in Detail view to Library"""
        items = self.lastSelectedItems
        for item in items:
            id = self.get_id_from_thumblist(item)
            txt = self.line_cat.text()
            pos = txt.find(",")
            if pos != -1:
                txt = txt[:pos]
            self.library.set_asset_cat(id, txt)

        self.library.save()

        return

    def user_update_name(self):
        """Apply change in Detail view to Library"""
        # if not self.edit:
        #     return
        items = self.lastSelectedItems
        for item in items:
            id = self.get_id_from_thumblist(item)
            self.library.set_asset_name(id, self.line_name.text())
        self.library.save()
        # self.update_views()
        return

    def user_update_tags(self):
        """Apply change in Detail view to Library"""
        # if not self.edit:
        #     return
        items = self.lastSelectedItems
        for item in items:
            id = self.get_id_from_thumblist(item)
            txt = self.line_tags.text()
            pos = txt.find(",")
            if pos != -1:
                txt = txt[-pos]
            self.library.set_asset_tag(id, txt)

        self.library.save()
        return

    def user_update_fav(self):
        """Apply change in Detail View - Favorite"""

        items = self.get_selected_items_from_thumblist_silent()
        if not items:
            return

        ids = []
        for item in items:
            id = self.get_id_from_thumblist(item)
            ids.append(id)
            if self.box_fav.checkState() is Qt.Checked:
                self.library.set_asset_fav(id, 1)
            else:
                self.library.set_asset_fav(id, 0)

        index = self.thumblist.selectedIndexes()

        self.library.save()

        for i in index:
            item = self.thumblist.itemFromIndex(i)
            self.thumblist.setCurrentItem(item)

    def user_update_date(self):

        items = self.lastSelectedItems
        for item in items:
            id = self.get_id_from_thumblist(item)
            self.library.update_asset_date(id)

    ###################################
    ########## UPDATE VIEWS ###########
    ###################################

    # Update Details view
    def update_details_view(self, item):
        """Update upon changes in Detail view"""
        if item is None:
            return

        items = self.get_selected_items_from_thumblist_silent()

        cat_flag = False
        tag_flag = False
        if items is not None:
            # Check all Selected assets for same Cat and Tag Values
            for x, item in enumerate(items):
                id = self.get_id_from_thumblist(item)
                curr_asset = self.library.get_asset_by_id(id)

                if x == 0:
                    cat = curr_asset.get_categories()
                    tags = curr_asset.get_tags()
                    fav = curr_asset.get_fav()
                else:
                    # Check Categories
                    if cat != curr_asset.get_categories():
                        cat_flag = True
                    # Check Tags
                    if tags != curr_asset.get_tags():
                        tag_flag = True

        id = self.get_id_from_thumblist(item)

        for asset in self.library.get_assets():
            if asset.get_id() == id:
                # set name
                self.line_name.setText(asset.get_name())
                # set cat
                if cat_flag:
                    self.line_cat.setText("Multiple Values")
                else:
                    self.line_cat.setText(", ".join(asset.get_categories()))
                # set tag
                if tag_flag:
                    self.line_tags.setText("Multiple Values")
                else:
                    self.line_tags.setText(", ".join(asset.get_tags()))
                # set fav
                if asset.get_fav() == 1:
                    self.box_fav.setCheckState(Qt.Checked)
                else:
                    self.box_fav.setCheckState(Qt.Unchecked)
                # set id
                self.line_id.setText(str(asset.get_id()))
                self.line_date.setText(asset.get_date())
        return

    # Update the Views when selection changes
    def update_selected_cat(self):
        """Update thumb view on change of category"""
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
        """Update cat view"""
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

    # Filter assets in Thumblist for Category
    def filter_view_category(self):
        """Filter Thumbview for selected Category"""
        # Filter Thumbnail View
        self.draw_assets = []
        for asset in self.library.get_assets():
            if self.selected_cat in asset.get_categories():
                self.draw_assets.append(asset)
        if not self.selected_cat:
            self.draw_assets = self.library.get_assets()
        return

    # Filter assets in Thumblist for Category
    def filter_view_filter(self):
        """Filter Thumbview for entered characters in filter-Line"""
        # Filter Thumbnail View
        if self.filter == "":
            return
        tmp = []
        if self.filter.startswith("*"):
            # Filter for tags
            curr_filter = self.filter[1:]
            for asset in self.draw_assets:
                if curr_filter in asset.get_tags():
                    tmp.append(asset)
        else:
            for asset in self.draw_assets:
                if self.filter in asset.get_name():
                    tmp.append(asset)
        self.draw_assets = tmp
        return

    # Update Thumbnail View
    def update_thumb_view(self):
        """Redraw the ThumbView with filters"""
        # Cleanup UI
        self.thumblist.clear()

        self.filter_view_category()  # Filter View by Category
        self.filter_view_filter()  # Filter View by Line Filter

        if self.draw_assets:
            for asset in self.draw_assets:
                # Pass Empty Default material
                # print(asset.get_id())
                if asset.get_id() == -1:
                    continue
                # Show only Favs
                if self.cb_FavsOnly.checkState() is Qt.Checked:
                    if asset.get_fav() == 0:
                        continue
                if self.cb_Redshift.isChecked():
                    if asset.get_renderer() != "Redshift":
                        continue
                elif self.cb_Mantra.isChecked():
                    if asset.get_renderer() != "Mantra":
                        continue
                elif self.cb_Arnold.isChecked():
                    if asset.get_renderer() != "Arnold":
                        continue
                elif self.cb_Octane.isChecked():
                    if asset.get_renderer() != "Octane":
                        continue
                elif self.cb_MatX.isChecked():
                    if asset.get_renderer() != "MatX":
                        continue

                img = (
                    self.library.get_path()
                    + self.prefs.get_img_dir()
                    + str(asset.get_id())
                    + self.prefs.get_img_ext()
                )

                favicon = hou.getenv("EGMATLIB") + "/def/Favorite.png"
                # Check if Thumb Exists and attach
                icon = None
                if os.path.isfile(img):
                    # Draw Star Icon on Top if Favorite
                    if asset.get_fav():
                        pm = QPixmap(
                            self.library.get_thumbSize(), self.library.get_thumbSize()
                        )

                        pm1 = QPixmap.fromImage(QImage(img)).scaled(
                            self.library.get_thumbSize(),
                            self.library.get_thumbSize(),
                            aspectMode=Qt.KeepAspectRatio,
                        )
                        pm2 = QPixmap.fromImage(QImage(favicon)).scaled(
                            self.library.get_thumbSize(),
                            self.library.get_thumbSize(),
                            aspectMode=Qt.KeepAspectRatio,
                        )
                        painter = QPainter(pm)
                        painter.setCompositionMode(QPainter.CompositionMode_Clear)
                        painter.fillRect(
                            0,
                            0,
                            self.library.get_thumbSize(),
                            self.library.get_thumbSize(),
                            QColor(0, 0, 0, 0),
                        )
                        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                        painter.drawPixmap(
                            0,
                            0,
                            self.library.get_thumbSize(),
                            self.library.get_thumbSize(),
                            pm1,
                        )

                        painter.drawPixmap(
                            0,
                            0,
                            self.library.get_thumbSize(),
                            self.library.get_thumbSize(),
                            pm2,
                        )
                        painter.end()
                        icon = QIcon(pm)

                    else:
                        pm = QPixmap(
                            self.library.get_thumbSize(), self.library.get_thumbSize()
                        )
                        painter = QPainter(pm)
                        painter.setCompositionMode(QPainter.CompositionMode_Clear)
                        painter.fillRect(
                            0,
                            0,
                            self.library.get_thumbSize(),
                            self.library.get_thumbSize(),
                            QColor(0, 0, 0, 0),
                        )
                        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

                        pixmap = QPixmap.fromImage(QImage(img)).scaled(
                            self.library.get_thumbSize(),
                            self.library.get_thumbSize(),
                            aspectMode=Qt.KeepAspectRatio,
                        )
                        painter.drawPixmap(
                            0,
                            0,
                            self.library.get_thumbSize(),
                            self.library.get_thumbSize(),
                            pixmap,
                        )
                        painter.end()
                        icon = QIcon(pm)
                else:
                    icon = self.default_icon()

                # Create entry in Thumblist
                # img_name = self.get_usd_by_id(asset.get_id())
                item = QListWidgetItem(icon, asset.get_name())

                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
                item.setData(Qt.UserRole, asset.get_id())  # Store ID with Thumb
                self.thumblist.addItem(item)
                self.thumblist.sortItems()

    # Create PlaceHolder Icon in case something goes wrong
    def default_icon(self):
        """Creates the default icon if something goes wrong"""
        # Generate Default Icon
        default_img = QImage(
            self.library.get_thumbSize(),
            self.library.get_thumbSize(),
            QImage.Format_RGB16,
        )
        default_img.fill(QColor(0, 0, 0))
        pixmap = QPixmap.fromImage(default_img).scaled(
            self.library.get_thumbSize(),
            self.library.get_thumbSize(),
            aspectMode=Qt.KeepAspectRatio,
        )
        default_icon = QIcon(pixmap)
        return default_icon

    ###################################
    ######### LIBRARY STUFF ###########
    ###################################

    # Rerender All Visible assets
    def update_all_assets(self):
        """Rerenders all assets in the library - The UI is blocked for the duration of the render"""
        if not hou.ui.displayConfirmation(
            "This can take a long time to render. Houdini will not be responsive during that time. Do you want continue rendering all visible assets?"
        ):
            return

        for i in range(self.thumblist.count()):
            item = self.thumblist.item(i)

            id = self.get_id_from_thumblist(item)
            self.render_thumbnail(id)

        self.update_thumb_view()
        hou.ui.displayMessage("Updating all Thumbnails finished")
        return

    # Rerender Selected Asset
    def update_single_asset(self, vp=False):
        """Rerenders a single Asset in the library - The UI is blocked for the duration of the render"""
        items = self.get_selected_items_from_thumblist()
        call = False
        for item in items:
            if not item:
                return
            id = self.get_id_from_thumblist(item)
            self.render_thumbnail(id)

        # self.update_thumb_view() :EGL
        if call:
            hou.ui.displayMessage("Thumbnail(s) updated")
        return

    def get_id_from_thumblist(self, item):
        """Return the id for the selected item in thumbview"""
        if item:
            return item.data(Qt.UserRole)
        else:
            return -1

    # Delete material from Library
    def delete_asset(self):
        """Deletes the selected material from Disk and Library"""
        if not hou.ui.displayConfirmation(
            "This will delete the selected material from Disk. Are you sure?"
        ):
            return

        items = self.get_selected_items_from_thumblist()

        for item in items:
            if not item:
                return

            id = self.get_id_from_thumblist(item)
            self.library.remove_asset(id)

        # Update View
        self.update_thumb_view()
        return

    # Get the selected material from Library
    def get_selected_item_from_thumblist(self):
        """Return the material for the selected item in thumbview"""
        item = self.thumblist.selectedItems()[0]
        if not item:
            hou.ui.displayMessage("No material selected")
            return None
        return item

    def get_selected_items_from_thumblist(self):
        """Return the material for the selected item in thumbview"""
        items = self.thumblist.selectedItems()
        if not items:
            hou.ui.displayMessage("No material selected")
            return None
        self.lastSelectedItems = items
        return items

    def get_selected_items_from_thumblist_silent(self):
        """Return the material for the selected item in thumbview"""
        items = self.thumblist.selectedItems()
        if not items:
            return None
        self.lastSelectedItems = items
        return items

    #  Saves a material to the Library
    def save_asset(self):
        """Saves the selected nodes (Network Editor) to the Library"""
        # Get Selected from Network View
        sel = hou.selectedNodes()
        # Check selection
        if not sel:
            hou.ui.displayMessage("No material selected")
            return
        self.get_material_info_user(sel)
        return

    def get_material_info_user(self, sel):
        """Query user for input upon material-save"""
        # Get Stuff from User
        dialog = MatLibDialogs.usdDialog()
        dialog.exec_()

        if dialog.canceled:
            return

        # Check if Category or Tags already exist
        if dialog.categories:
            self.library.check_add_category(dialog.categories)
        if dialog.tags:
            self.library.check_add_tags(dialog.tags)

        for asset in sel:
            self.library.add_asset(asset, dialog.categories, dialog.tags, dialog.fav)
        self.update_views()
        return

    def import_assets(self):
        items = self.get_selected_items_from_thumblist()
        for item in items:
            self.import_asset(item)
        return

    #  Import material to Scene
    def import_asset(self, sel=None):
        """Import Material to scene"""
        if not sel:
            item = self.thumblist.selectedItems()[0]
        else:
            item = sel

        if not item:
            hou.ui.displayMessage("No Asset selected")
            return

        id = self.get_id_from_thumblist(item)

        return self.library.import_asset_to_scene(id)

    def render_thumbnail(self, id):

        builder = self.library.import_asset_to_scene(id)
        self.library.create_thumbnail(builder, id)
        builder.destroy()

        return
