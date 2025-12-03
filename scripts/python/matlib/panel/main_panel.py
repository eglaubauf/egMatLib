import os
import shutil
import sys
import subprocess
import importlib
from PySide6 import QtWidgets, QtGui, QtCore, QtUiTools

import hou

from matlib.core import matlib_core
from matlib.dialogs import (
    about_dialog,
    material_dialog,
    prefs_dialog,
    usd_dialog,
)
from matlib.prefs import main_prefs
from matlib.helpers import ui_helpers

# Set Develop flag to reload everthing properly
importlib.reload(matlib_core)
importlib.reload(main_prefs)
importlib.reload(ui_helpers)

importlib.reload(material_dialog)
importlib.reload(about_dialog)
importlib.reload(prefs_dialog)
importlib.reload(usd_dialog)


def save_material(node: hou.Node) -> None:
    # Call from RC-Menus in Network Pane
    # TODO: Move
    # Initialize
    pref = main_prefs.Prefs()
    path = pref.get_dir() + "/"
    path = path.replace("\\", "/")

    # Save new Data to Library
    library = matlib_core.MaterialLibrary()
    library.load(path, pref)

    # Get Stuff from User
    dialog = usd_dialog.UsdDialog()
    r = dialog.exec_()
    if dialog.canceled or not r:
        return

    # Check if Category or Tags already exist
    if dialog.categories:
        library.check_add_category(dialog.categories)
    if dialog.tags:
        library.check_add_tags(dialog.tags)

    library.add_asset(node, dialog.categories, dialog.tags, dialog.fav)

    library.save()

    # Update Widget
    for pane_tab in hou.ui.paneTabs():  # type: ignore
        if pane_tab.type() == hou.paneTabType.PythonPanel:
            if pane_tab.label() == "MatLib":
                panel = pane_tab.activeInterfaceRootWidget()
                panel.update_external()
                return


class MatLibPanel(QtWidgets.QWidget):
    def __init__(self) -> None:
        super(MatLibPanel, self).__init__()

        # Initialize
        self.script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        self.prefs = main_prefs.Prefs()
        path = self.prefs.get_dir()
        if not path.endswith("/"):
            path = path + "/"

        self.library = None
        self.createview()

        self.selected_cat = None
        self.filter = ""

        self.active_row = None
        self.last_selected_items = []
        self.draw_assets = []
        self.active = False
        self.active_item = None
        self.edit = False

        if os.path.exists(path):
            self.open(path)

        self.update_context()

    def open(self, path=None) -> None:

        if not path:
            path = self.prefs.get_dir()
            if not path.endswith("/"):
                path = path + "/"
            path = hou.ui.selectFile(file_type=hou.fileType.Directory)
            path = hou.expandString(path)

        # Get Dir from User
        count = 0
        while count < 1:
            if os.path.exists(path):
                self.prefs.set_dir(path)
                self.prefs.save()
                count = 3
            elif path == "":
                return
            else:
                hou.ui.displayMessage("Please choose a valid path")  # type: ignore
                path = hou.ui.selectFile(file_type=hou.fileType.Directory)
                path = hou.expandString(path)
            count += 1
        # Return if still not a valid path
        if path == "":
            return

        path = path.replace("\\", "/")
        new_folder = False
        if not os.path.exists(path + "/library.json"):
            oldpath = (
                hou.getenv("EGMATLIB") + "/scripts/python/matlib/res/def/library.json"
            )
            shutil.copy(oldpath, path + "/library.json")
            new_folder = True
        if not os.path.exists(path + self.prefs.get_img_dir()):
            os.mkdir(path + self.prefs.get_img_dir())
            os.mkdir(path + self.prefs.get_asset_dir())
            new_folder = True
        if new_folder:
            msg = "A new library has been created successfully"
            hou.ui.displayMessage(msg)  # type: ignore
        self.path = path
        # Create Library
        self.library = matlib_core.MaterialLibrary()
        self.library.load(path, self.prefs)

        self.draw_assets = self.library.assets  # Filterered assets for Views
        self.update_views()

    def update_external(self) -> None:
        if self.library:
            self.library.load(self.path, self.prefs)
            self.update_views()
        else:
            hou.ui.displayMessage("Please open a library first")  # type: ignore
        return

    def update_views(self) -> None:
        self.update_ui()
        self.update_thumb_view()
        self.update_cat_view()

    def update_ui(self) -> None:
        if self.cb_mantra.isChecked():
            self.radio_usd.setDisabled(False)
            self.radio_current.setDisabled(False)
        if self.cb_matx.isChecked():
            self.radio_usd.setDisabled(False)
            self.radio_current.setDisabled(False)
        if self.cb_arnold.isChecked():
            self.radio_default.setChecked(True)
            self.radio_usd.setDisabled(True)
            self.radio_current.setDisabled(True)
        if self.cb_redshift.isChecked():
            self.radio_default.setChecked(True)
            self.radio_usd.setDisabled(True)
            self.radio_current.setDisabled(True)
        if self.cb_octane.isChecked():
            self.radio_default.setChecked(True)
            self.radio_usd.setDisabled(True)
            self.radio_current.setDisabled(True)

    def toggle_catview(self) -> None:
        if self.action_catview.isChecked():
            self.cat_list.setVisible(True)
            self.action_catview.setChecked(True)
        else:
            self.cat_list.setVisible(False)
            self.action_catview.setChecked(False)

    def toggle_catview_rc(self) -> None:
        if not self.action_catview.isChecked():
            self.cat_list.setVisible(True)
            self.action_catview.setChecked(True)
        else:
            self.cat_list.setVisible(False)
            self.action_catview.setChecked(False)

    def toggle_detailsview(self) -> None:
        details_widget = self.ui.findChild(QtWidgets.QWidget, "details_widget")

        if self.action_detailsview.isChecked():
            details_widget.setHidden(False)
            self.action_detailsview.setChecked(True)
        else:
            details_widget.setHidden(True)
            self.action_detailsview.setChecked(False)

    def toggle_detailsview_rc(self) -> None:
        details_widget = self.ui.findChild(QtWidgets.QWidget, "details_widget")

        if not self.action_detailsview.isChecked():
            details_widget.setHidden(False)
            self.action_detailsview.setChecked(True)
        else:
            details_widget.setHidden(True)
            self.action_detailsview.setChecked(False)

    # View Stuff
    def createview(self) -> None:
        """Creates the panel-view on load"""
        # Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QtCore.QFile(self.script_path + "/ui/matlib.ui")
        file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

        # Helper for Table_Trigger
        self.active = False

        # Load Ui Element so self
        self.menu = self.ui.findChild(QtWidgets.QMenuBar, "menubar")
        self.menuGoto = self.ui.findChild(QtWidgets.QMenu, "menu_file")
        self.action_prefs = self.ui.findChild(QtGui.QAction, "action_prefs")
        self.action_prefs.triggered.connect(self.show_prefs)

        self.menu_view = self.ui.findChild(QtWidgets.QMenu, "menu_view")
        self.action_catview = self.ui.findChild(QtGui.QAction, "action_show_cat")
        self.action_catview.triggered.connect(self.toggle_catview)

        self.action_detailsview = self.ui.findChild(
            QtGui.QAction, "action_show_details"
        )
        self.action_detailsview.triggered.connect(self.toggle_detailsview)

        self.action_cleanup_db = self.ui.findChild(QtGui.QAction, "action_cleanup_db")
        self.action_cleanup_db.triggered.connect(self.cleanup_db)
        self.action_open_folder = self.ui.findChild(QtGui.QAction, "action_open_folder")
        self.action_open_folder.triggered.connect(self.open_usdlib_folder)

        self.action_about = self.ui.findChild(QtGui.QAction, "action_about")
        self.action_about.triggered.connect(self.show_about)

        self.action_open = self.ui.findChild(QtGui.QAction, "action_open")
        self.action_open.triggered.connect(self.open)

        # TODO: FUTURE
        # self.action_import_folder = self.ui.findChild(QtGui.QAction, "action_import_folder")
        # self.action_import_folder.triggered.connect(self.import_folder)

        self.action_import_files = self.ui.findChild(
            QtGui.QAction, "action_import_files"
        )
        self.action_import_files.triggered.connect(self.import_files)

        self.action_force_update = self.ui.findChild(
            QtGui.QAction, "action_force_update"
        )
        self.action_force_update.triggered.connect(self.update_external)

        self.thumblist = self.ui.findChild(QtWidgets.QListWidget, "listw_matview")
        # self.thumblist.setIconSize(
        #     QtCore.QSize(self.library.thumbsize, self.library.thumbsize)
        # )
        self.thumblist.doubleClicked.connect(self.import_asset)
        self.thumblist.itemPressed.connect(self.update_details_view)
        # self.thumblist.setGridSize(
        #     QtCore.QSize(self.library.thumbsize + 10, self.library.thumbsize + 40)
        # )
        self.thumblist.setContentsMargins(0, 0, 0, 0)
        self.thumblist.setSortingEnabled(True)

        # Category UI
        self.cat_list = self.ui.findChild(QtWidgets.QListWidget, "listw_catview")
        self.cat_list.clicked.connect(self.update_selected_cat)

        # FILTER UI
        self.line_filter = self.ui.findChild(QtWidgets.QLineEdit, "line_filter")
        self.line_filter.textChanged.connect(self.filter_thumb_view_user)

        # Updated Details UI
        self.details = self.ui.findChild(QtWidgets.QTableWidget, "details_widget")
        self.line_name = self.ui.findChild(QtWidgets.QLineEdit, "line_name")
        self.line_cat = self.ui.findChild(QtWidgets.QLineEdit, "line_cat")
        self.line_tags = self.ui.findChild(QtWidgets.QLineEdit, "line_tags")
        self.line_id = self.ui.findChild(QtWidgets.QLineEdit, "line_id")
        self.line_render = self.ui.findChild(QtWidgets.QLineEdit, "line_render")
        self.line_date = self.ui.findChild(QtWidgets.QLineEdit, "line_date")
        self.box_fav = self.ui.findChild(QtWidgets.QCheckBox, "cb_set_fav")
        self.btn_update = self.ui.findChild(QtWidgets.QPushButton, "btn_update")
        self.btn_update.clicked.connect(self.user_update_asset)

        # Options
        self.cb_favsonly = self.ui.findChild(QtWidgets.QCheckBox, "cb_FavsOnly")
        self.cb_favsonly.stateChanged.connect(self.update_views)

        # Material
        self.cb_redshift = self.ui.findChild(QtWidgets.QRadioButton, "cb_Redshift")
        self.cb_mantra = self.ui.findChild(QtWidgets.QRadioButton, "cb_Mantra")
        self.cb_arnold = self.ui.findChild(QtWidgets.QRadioButton, "cb_Arnold")
        self.cb_octane = self.ui.findChild(QtWidgets.QRadioButton, "cb_Octane")
        self.cb_matx = self.ui.findChild(QtWidgets.QRadioButton, "cb_MatX")

        self.cb_showcat = self.ui.findChild(QtWidgets.QCheckBox, "cb_showCat")

        self.cb_favsonly.stateChanged.connect(self.update_views)

        self.cb_redshift.toggled.connect(self.update_views)
        self.cb_mantra.toggled.connect(self.update_views)
        self.cb_arnold.toggled.connect(self.update_views)
        self.cb_octane.toggled.connect(self.update_views)
        self.cb_matx.toggled.connect(self.update_views)

        # Context Options
        self.radio_current = self.ui.findChild(QtWidgets.QRadioButton, "radio_current")
        self.radio_current.toggled.connect(self.update_context)

        self.radio_usd = self.ui.findChild(QtWidgets.QRadioButton, "radio_USD")
        self.radio_usd.toggled.connect(self.update_context)

        self.radio_default = self.ui.findChild(QtWidgets.QRadioButton, "radio_default")
        self.radio_default.toggled.connect(self.update_context)

        # IconSize Slider
        self.slide_iconsize = self.ui.findChild(QtWidgets.QSlider, "slide_iconSize")
        self.slide_iconsize.setVisible(False)

        # Set Up Clickable Slider
        self.click_slider = ui_helpers.ClickSlider()
        self.click_slider.setOrientation(QtCore.Qt.Horizontal)
        self.click_slider.setMinimum(0)
        self.click_slider.setMaximum(512)
        self.click_slider.setSingleStep(50)
        self.click_slider.setPageStep(50)
        self.slider_layout = self.ui.findChild(QtWidgets.QVBoxLayout, "slider_layout")
        self.slider_layout.addWidget(self.click_slider)
        self.click_slider.valueChanged.connect(self.slide)
        if self.library:
            self.click_slider.setValue(self.library.thumbsize)

        # RC Menus
        self.thumblist.customContextMenuRequested.connect(self.thumblist_rc_menu)
        self.cat_list.customContextMenuRequested.connect(self.catlist_rc_menu)

        self.a_folder = self.ui.findChild(QtGui.QAction, "action_import_folder")
        self.a_folder.setDisabled(True)
        self.a_folder.setVisible(False)

        self.a_files = self.ui.findChild(QtGui.QAction, "action_import_files")
        self.a_files.setDisabled(True)
        self.a_files.setVisible(False)

        # self.menu_import = self.ui.findChild(QtWidgets.QMenu, "menuImport")
        # self.menu_import.setDisabled(True)
        # self.menu_import.setVisible(False)

        # set main layout and attach to widget
        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addWidget(self.ui)
        mainlayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainlayout)

        # Cleanup UI
        self.setStyleSheet("""  font-family: Lato; """)
        self.menu.setStyleSheet(""" font-family: Lato; """)
        self.menuGoto.setStyleSheet("""  font-family: Lato; """)
        # self.menu_import.setStyleSheet("""  font-family: Lato; """)

    def update_context(self) -> None:
        if not self.library:
            return
        if self.radio_usd.isChecked():
            self.library.context = hou.node("/stage")
        elif self.radio_current.isChecked():
            curr_node = self.get_current_network_node()
            if curr_node is None:
                self.library.context = hou.node("/stage")
                return
            else:
                self.library.context = curr_node
        elif self.radio_default.isChecked():
            self.library.context = hou.node("/mat")

    def get_current_network_node(self) -> hou.Node | None:
        """Return thre current Node in the Network Editor"""
        for pt in hou.ui.paneTabs():  # type: ignore
            if pt.type() == hou.paneTabType.NetworkEditor:
                return pt.currentNode()
        return None

    # RC Menus
    def thumblist_rc_menu(self) -> None:
        cmenu = QtWidgets.QMenu(self)

        action_import = cmenu.addAction("Import to Scene")
        action_toggle_fav = cmenu.addAction("Toggle Favorite")
        action_render = cmenu.addAction("Rerender Thumbnail")
        action_renderall = cmenu.addAction("Render All Thumbnails")
        action_thumb_viewport = cmenu.addAction("Thumbnail from Viewport")
        cmenu.addSeparator()
        action_delete = cmenu.addAction("Delete Entry")
        cmenu.addSeparator()
        action_toggle_cats = cmenu.addAction("Toggle Cat View")
        action_toggle_details = cmenu.addAction("Toggle Details View")
        action = cmenu.exec_(QtGui.QCursor.pos())

        if action == action_delete:
            self.delete_asset()
        elif action == action_render:
            self.update_single_asset()
        elif action == action_import:
            self.import_assets()
        elif action == action_renderall:
            self.update_all_assets()
        elif action == action_thumb_viewport:
            self.update_single_asset()
        elif action == action_toggle_fav:
            self.toggle_fav()
        elif action == action_toggle_details:
            self.toggle_detailsview_rc()
        elif action == action_toggle_cats:
            self.toggle_catview_rc()

        self.update_views()

    def catlist_rc_menu(self) -> None:
        cmenu = QtWidgets.QMenu(self)

        action_remove = cmenu.addAction("Remove Category")
        action_rename = cmenu.addAction("Rename Entry")
        action_add = cmenu.addAction("Add Category")
        action = cmenu.exec_(QtGui.QCursor.pos())

        if action == action_remove:
            self.rmv_category_user()
        elif action == action_rename:
            self.rename_category_user()
        elif action == action_add:
            self.add_category_user()
        return

    def toggle_fav(self) -> None:
        items = self.get_selected_items_from_thumblist()
        if not items:
            return
        for item in items:
            curr_id = self.get_id_from_thumblist(item)

            if self.library.get_asset_fav(curr_id):
                self.library.set_asset_fav(curr_id, False)
            else:
                self.library.set_asset_fav(curr_id, True)

        self.update_details_view(items[0])
        self.update_views()

    # def import_folder(self):
    #     self.h = importMat.Controller()
    #     self.h.show()
    #     self.h.finished.connect(self.import_folder_finished)

    def import_folder_finished(self) -> None:
        #  finalize import by adding the created materials to the library
        materials = self.h.core.get_new_materials()
        nodes = []
        for mat in materials:
            if mat.getNode().type().name() == "materiallibrary":
                nodes.append(mat.get_output())
            else:
                nodes.append(mat.getNode())
        self.get_material_info_user(nodes)

    def import_files(self) -> None:
        msg = "Choose Material type to create"
        buttons = ["Principled", "MaterialX", "Cancel"]
        choice = hou.ui.displayMessage(msg, buttons)  # type: ignore
        if choice < 0 or choice == len(buttons) - 1:
            return

    def import_files_finished(self) -> None:
        # finalize import by adding the created materials to the library
        mat = self.h.core.get_new_material()
        nodes = []
        if mat.getNode().type().name() == "materiallibrary":
            nodes.append(mat.get_output())
        else:
            nodes.append(mat.getNode())
        self.get_material_info_user(nodes)

    # User Stuff
    def show_about(self) -> None:
        about = about_dialog.AboutDialog()
        about.exec_()

    def show_prefs(self) -> None:
        if not self.library:
            hou.ui.displayMessage("Please open a library first")  # type: ignore
            return
        prefs = prefs_dialog.PrefsDialog(self.library, self.prefs)
        prefs.exec_()

        if prefs.canceled:
            return

        # Update Thumblist Grid
        self.thumblist.setIconSize(
            QtCore.QSize(self.library.thumbsize, self.library.thumbsize)
        )
        self.thumblist.setGridSize(
            QtCore.QSize(self.library.thumbsize + 10, self.library.thumbsize + 40)
        )
        self.update_views()

    # Remove image thumbs and .asset-files not used in material library.
    def cleanup_files(self) -> None:
        assets = self.library.assets
        img_path = os.path.join(self.path, self.prefs.get_img_dir())
        asset_path = os.path.join(self.path, self.prefs.get_asset_dir())

        img_thumbs = os.listdir(img_path)
        asset_files = os.listdir(asset_path)

        for img in img_thumbs:
            asset_id = img.split(".")[0]
            # found = False
            for asset in assets:
                if asset.mat_id == int(asset_id):
                    # found = True
                    break
            # if not found:
            #     if asset.mat_id > 0:
            #         try:
            #             os.remove(os.path.join(img_path, img))
            #             print("File: " + os.path.join(img_path, img) + " removed")
            #             self.library.remove_asset(id)
            #         except:
            #             pass

        for m in asset_files:
            asset_id = m.split(".")[0]
            if "img" in asset_id:
                return
            # found = False
            for asset in assets:
                if asset.mat_id == int(asset_id):
                    # found = True
                    break
            # if not found:
            #     if asset.mat_id > 0:
            #         try:
            #             os.remove(os.path.join(asset_path, m))
            #             print("File: " + os.path.join(asset_path, m) + " removed")
            #             self.library.remove_asset(id)
            #         except:
            #             pass

        for asset in assets:
            path = asset.path
            if not os.path.exists(path):
                try:
                    # os.remove(os.path.join(asset_path, m))
                    print("File: " + path + " removed")
                    self.library.remove_asset(asset.mat_id)
                except OSError:
                    pass
        self.update_thumb_view()
        return

    def cleanup_db(self) -> None:
        if not self.library:
            hou.ui.displayMessage("Please open a library first")  # type: ignore
            return
        assets = self.library.assets
        mark_rmv = 0
        mark_render = 0

        for asset in assets:
            if asset.mat_id > 0:
                interface_path = os.path.join(
                    self.path,
                    self.prefs.get_asset_dir(),
                    str(asset.mat_id) + ".interface",
                )
                mat_path = os.path.join(
                    self.path, self.prefs.get_asset_dir(), str(asset.mat_id) + ".mat"
                )
                img_path = os.path.join(
                    self.path,
                    self.prefs.get_img_dir(),
                    str(asset.mat_id) + self.prefs.get_img_ext(),
                )

                # asset_path = asset.path
                if not os.path.exists(interface_path):
                    print("Asset %d missing on disk. Removing.", asset.mat_id)
                    mark_rmv = 1
                    self.library.remove_asset(asset.mat_id)
                if not os.path.exists(mat_path):
                    print("Asset %d missing on disk. Removing.", asset.mat_id)
                    mark_rmv = 1
                    self.library.remove_asset(asset.mat_id)
                if not os.path.exists(img_path):
                    mark_render = 1
                    print(
                        f"Image for Asset { asset.mat_id} missing on disk. Needs Rendering."
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
                        f"Lonely File at {os.path.join(mats_path, f)} found. Removing from disk"
                    )
                    os.remove(os.path.join(mats_path, f))
                    mark_lone = 1

        if mark_rmv:
            hou.ui.displayMessage(
                "Assets have been cleaned up. See python shell for details"  # type: ignore
            )
        if mark_render:
            hou.ui.displayMessage(
                "Missing images have been found. Rerender thumbs required"  # type: ignore
            )
        if mark_lone:
            hou.ui.displayMessage("Lone files have been found and removed from disk.")  # type: ignore

        self.update_thumb_view()

    def render_missing(self) -> None:
        if not self.library:
            hou.ui.displayMessage("Please open a library first")  # type: ignore
            return
        assets = self.library.assets

        for asset in assets:
            if asset.mat_id > 0:
                img_path = os.path.join(
                    self.path,
                    self.prefs.get_img_dir(),
                    str(asset.mat_id) + self.prefs.get_img_ext(),
                )
                # print(img_path)
                asset_path = asset.path

                # Only check for img and asset for backwards compatibility
                if os.path.exists(img_path) and os.path.exists(asset_path):
                    # All clear - do nothing
                    continue
                else:
                    if not os.path.exists(img_path):
                        print("Render Thumbnail for Asset " + asset.name)
                        self.render_thumbnail(asset.mat_id)
                    elif not os.path.exists(asset_path):
                        print("Asset missing on disk. Removing.")
                        self.library.remove_asset(asset.mat_id)
                    self.update_thumb_view()
        return

    def open_usdlib_folder(self) -> None:
        if not self.library:
            hou.ui.displayMessage("Please open a library first")  # type: ignore
            return
        lib_dir = self.path
        lib_dir.encode("unicode_escape")

        if sys.platform == "linux" and sys.platform == "linux2":  # Linux
            os.startfile(lib_dir)
            return
        elif sys.platform == "darwin":  # MacOS
            opener = "open"
            subprocess.call([opener, lib_dir])
        elif sys.platform == "win32":  # MacOS:  # Windows
            os.startfile(lib_dir)

    # User Adds Category with Button
    def add_category_user(self) -> None:
        choice, cat = hou.ui.readInput("Please enter the new category name:")  # type: ignore
        if choice:  # Return if no
            return
        self.library.check_add_category(cat)
        self.library.save()
        self.update_views()

    # User Removes Category with Button
    def rmv_category_user(self) -> None:
        """Removes a category - called by user change in UI"""
        rmv_item = self.cat_list.selectedItems()
        # Prevent Deletion of "All" - Category
        if rmv_item[0].text() == "All":
            return

        self.library.remove_category(rmv_item[0].text())

        self.library.save()
        self.update_views()

    def rename_category_user(self) -> None:
        """Renames a category - called by user change in UI"""
        choice, cat = hou.ui.readInput("Please enter the new category name:")  # type: ignore
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
    def filter_thumb_view_user(self) -> None:
        """Get Filter from user and trigger view update"""
        self.filter = self.line_filter.text()
        self.update_thumb_view()

    def listen_entry_from_detail(self, item: QtWidgets.QListWidgetItem) -> None:
        """Set Detail view to Edit Mode"""
        self.active = True
        self.active_item = item

    # Update Views
    def user_update_asset(self) -> None:
        self.user_update_cats()
        self.user_update_name()
        self.user_update_tags()
        self.user_update_fav()
        self.user_update_date()
        self.update_views()

    def user_update_cats(self) -> None:
        """Apply change in Detail view to Library"""
        items = self.last_selected_items
        for item in items:
            asset_id = self.get_id_from_thumblist(item)
            txt = self.line_cat.text()
            pos = txt.find(",")
            if pos != -1:
                txt = txt[:pos]
            self.library.set_asset_cat(asset_id, txt)

        self.library.save()

    def user_update_name(self) -> None:
        """Apply change in Detail view to Library"""
        items = self.last_selected_items
        for item in items:
            asset_id = self.get_id_from_thumblist(item)
            self.library.set_asset_name_by_id(asset_id, self.line_name.text())
        self.library.save()

    def user_update_tags(self) -> None:
        """Apply change in Detail view to Library"""
        # if not self.edit:
        #     return
        items = self.last_selected_items
        for item in items:
            asset_id = self.get_id_from_thumblist(item)
            txt = self.line_tags.text()
            pos = txt.find(",")
            if pos != -1:
                txt = txt[-pos]
            self.library.set_asset_tag(asset_id, txt)

        self.library.save()

    def user_update_fav(self) -> None:
        """Apply change in Detail View - Favorite"""

        items = self.get_selected_items_from_thumblist_silent()
        if not items:
            return

        asset_ids = []
        for item in items:
            asset_id = self.get_id_from_thumblist(item)
            asset_ids.append(asset_id)
            if self.box_fav.checkState() is QtCore.Qt.Checked:
                self.library.set_asset_fav(asset_id, True)
            else:
                self.library.set_asset_fav(asset_id, False)

        index = self.thumblist.selectedIndexes()

        self.library.save()

        for i in index:
            item = self.thumblist.itemFromIndex(i)
            self.thumblist.setCurrentItem(item)

    def user_update_date(self) -> None:
        items = self.last_selected_items
        for item in items:
            asset_id = self.get_id_from_thumblist(item)
            self.library.update_asset_date(asset_id)

    # Update Views Section
    # Update Details view
    def update_details_view(self, item: QtWidgets.QListWidgetItem) -> None:
        """Update upon changes in Detail view"""
        if item is None:
            return

        items = self.get_selected_items_from_thumblist_silent()

        cat_flag = False
        tag_flag = False
        cat = ""
        tags = ""
        if items is not None:
            # Check all Selected assets for same Cat and Tag Values
            for x, item in enumerate(items):
                asset_id = self.get_id_from_thumblist(item)
                curr_asset = self.library.get_asset_by_id(asset_id)

                if x == 0:
                    cat = curr_asset.categories
                    tags = curr_asset.tags
                    # fav = curr_asset.get_fav()
                else:
                    # Check Categories
                    if cat != curr_asset.categories:
                        cat_flag = True
                    # Check Tags
                    if tags != curr_asset.tags:
                        tag_flag = True

        asset_id = self.get_id_from_thumblist(item)

        for asset in self.library.assets:
            if asset.mat_id == asset_id:
                # set name
                self.line_name.setText(asset.name)
                # set cat
                if cat_flag:
                    self.line_cat.setText("Multiple Values")
                else:
                    self.line_cat.setText(", ".join(asset.categories))
                # set tag
                if tag_flag:
                    self.line_tags.setText("Multiple Values")
                else:
                    self.line_tags.setText(", ".join(asset.tags))
                # set fav
                if asset.fav == 1:
                    self.box_fav.setCheckState(QtCore.Qt.Checked)
                else:
                    self.box_fav.setCheckState(QtCore.Qt.Unchecked)
                # set id
                self.line_id.setText(str(asset.mat_id))
                self.line_date.setText(str(asset.date))
        return

    # Update the Views when selection changes
    def update_selected_cat(self) -> None:
        """Update thumb view on change of category"""
        self.selected_cat = None
        items = self.cat_list.selectedItems()
        if len(items) == 1:
            if items[0].text() == "All":
                self.selected_cat = None
                self.update_thumb_view()
            else:
                self.selected_cat = items[0].text()
                self.update_thumb_view()

    # Update Category View
    def update_cat_view(self) -> None:
        """Update cat view"""
        self.cat_list.clear()
        for cat in self.library.categories:
            item = QtWidgets.QListWidgetItem(cat)
            self.cat_list.addItem(item)

        begin = self.cat_list.findItems("All", QtCore.Qt.MatchExactly)[0]

        if sys.platform == "linux" or sys.platform == "linux2":
            begin.setText("000_All")
        else:
            begin.setText("___All")
        self.cat_list.sortItems()
        begin.setText("All")
        self.thumblist.sortItems()

    # Filter assets in Thumblist for Category
    def filter_view_category(self) -> None:
        """Filter Thumbview for selected Category"""
        # Filter Thumbnail View
        self.draw_assets = []
        for asset in self.library.assets:
            if self.selected_cat in asset.categories:
                self.draw_assets.append(asset)
        if not self.selected_cat:
            self.draw_assets = self.library.assets

    # Filter assets in Thumblist for Category
    def filter_view_filter(self) -> None:
        """Filter Thumbview for entered characters in filter-Line"""
        # Filter Thumbnail View
        if self.filter == "":
            return
        tmp = []
        if self.filter.startswith("*"):
            # Filter for tags
            curr_filter = self.filter[1:]
            for asset in self.draw_assets:
                if curr_filter in asset.tags:
                    tmp.append(asset)
        else:
            for asset in self.draw_assets:
                if self.filter in asset.name:
                    tmp.append(asset)
        self.draw_assets = tmp

    # Update Thumbnail View
    def update_thumb_view(self) -> None:
        """Redraw the ThumbView with filters"""
        # Cleanup UI
        self.thumblist.clear()

        self.filter_view_category()  # Filter View by Category
        self.filter_view_filter()  # Filter View by Line Filter

        if self.draw_assets:
            for asset in self.draw_assets:
                # Pass Empty Default material
                if asset.mat_id == -1:
                    continue
                # Show only Favs
                if self.cb_favsonly.checkState() is QtCore.Qt.Checked:
                    if asset.fav == 0:
                        continue
                if self.cb_redshift.isChecked():
                    if asset.renderer != "Redshift":
                        continue
                elif self.cb_mantra.isChecked():
                    if asset.renderer != "Mantra":
                        continue
                elif self.cb_arnold.isChecked():
                    if asset.renderer != "Arnold":
                        continue
                elif self.cb_octane.isChecked():
                    if asset.renderer != "Octane":
                        continue
                elif self.cb_matx.isChecked():
                    if asset.renderer != "MatX":
                        continue

                img = (
                    self.library.path
                    + self.prefs.get_img_dir()
                    + str(asset.mat_id)
                    + self.prefs.get_img_ext()
                )

                favicon = hou.getenv("EGMATLIB") + "/def/Favorite.png"
                # Check if Thumb Exists and attach
                icon = None
                if os.path.isfile(img):
                    # Draw Star Icon on Top if Favorite
                    if asset.fav:
                        pm = QtGui.QPixmap(
                            self.library.thumbsize, self.library.thumbsize
                        )

                        pm1 = QtGui.QPixmap.fromImage(QtGui.QImage(img)).scaled(
                            self.library.thumbsize,
                            self.library.thumbsize,
                            aspectMode=QtCore.Qt.KeepAspectRatio,
                        )
                        pm2 = QtGui.QPixmap.fromImage(QtGui.QImage(favicon)).scaled(
                            self.library.thumbsize,
                            self.library.thumbsize,
                            aspectMode=QtCore.Qt.KeepAspectRatio,
                        )
                        painter = QtGui.QPainter(pm)
                        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
                        painter.fillRect(
                            0,
                            0,
                            self.library.thumbsize,
                            self.library.thumbsize,
                            QtGui.QColor(0, 0, 0, 0),
                        )
                        painter.setCompositionMode(
                            QtGui.QPainter.CompositionMode_SourceOver
                        )
                        painter.drawPixmap(
                            0,
                            0,
                            self.library.thumbsize,
                            self.library.thumbsize,
                            pm1,
                        )

                        painter.drawPixmap(
                            0,
                            0,
                            self.library.thumbsize,
                            self.library.thumbsize,
                            pm2,
                        )
                        painter.end()
                        icon = QtGui.QIcon(pm)

                    else:
                        pm = QtGui.QPixmap(
                            self.library.thumbsize, self.library.thumbsize
                        )
                        painter = QtGui.QPainter(pm)
                        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
                        painter.fillRect(
                            0,
                            0,
                            self.library.thumbsize,
                            self.library.thumbsize,
                            QtGui.QColor(0, 0, 0, 0),
                        )
                        painter.setCompositionMode(
                            QtGui.QPainter.CompositionMode_SourceOver
                        )

                        pixmap = QtGui.QPixmap.fromImage(QtGui.QImage(img)).scaled(
                            self.library.thumbsize,
                            self.library.thumbsize,
                            aspectMode=QtCore.Qt.KeepAspectRatio,
                        )
                        painter.drawPixmap(
                            0,
                            0,
                            self.library.thumbsize,
                            self.library.thumbsize,
                            pixmap,
                        )
                        painter.end()
                        icon = QtGui.QIcon(pm)
                else:
                    icon = self.default_icon()

                # Create entry in Thumblist
                # img_name = self.get_usd_by_id(asset.mat_id)
                item = QtWidgets.QListWidgetItem(icon, asset.name)

                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)
                item.setData(QtCore.Qt.UserRole, asset.mat_id)  # Store ID with Thumb
                self.thumblist.addItem(item)
                self.thumblist.sortItems()

    # Create PlaceHolder Icon in case something goes wrong
    def default_icon(self) -> QtGui.QIcon:
        """Creates the default icon if something goes wrong"""
        # Generate Default Icon
        default_img = QtGui.QImage(
            self.library.thumbsize,
            self.library.thumbsize,
            QtGui.QImage.Format_RGB16,
        )
        default_img.fill(QtGui.QColor(0, 0, 0))
        pixmap = QtGui.QPixmap.fromImage(default_img).scaled(
            self.library.thumbsize,
            self.library.thumbsize,
            aspectMode=QtCore.Qt.KeepAspectRatio,
        )
        default_icon = QtGui.QIcon(pixmap)
        return default_icon

    # Library Stuffs
    # Rerender All Visible assets
    def update_all_assets(self) -> None:
        """Rerenders all assets in the library - The UI is blocked for the duration of the render"""
        if not self.library:
            hou.ui.displayMessage("Please open a library first")  # type: ignore
            return

        if not hou.ui.displayConfirmation(
            """This can take a long time to render. Houdini will not be responsive during that time.
            Do you want continue rendering all visible assets?"""  # type: ignore
        ):  # type: ignore
            return

        for i in range(self.thumblist.count()):
            item = self.thumblist.item(i)

            asset_id = self.get_id_from_thumblist(item)
            self.render_thumbnail(asset_id)

        self.update_thumb_view()
        hou.ui.displayMessage("Updating all Thumbnails finished")  # type: ignore

    # Rerender Selected Asset
    def update_single_asset(self) -> None:
        """Rerenders a single Asset in the library - The UI is blocked for the duration of the render"""
        items = self.get_selected_items_from_thumblist()
        if not items:
            return
        call = False
        for item in items:
            if not item:
                return
            asset_id = self.get_id_from_thumblist(item)
            self.render_thumbnail(asset_id)

        # self.update_thumb_view() :EGL
        if call:
            hou.ui.displayMessage("Thumbnail(s) updated")  # type: ignore

    def get_id_from_thumblist(self, item: QtWidgets.QListWidgetItem) -> str:
        """Return the id for the selected item in thumbview"""
        if item:
            return str(item.data(QtCore.Qt.UserRole))
        else:
            return ""

    # Delete material from Library
    def delete_asset(self) -> None:
        """Deletes the selected material from Disk and Library"""
        if not hou.ui.displayConfirmation(
            "This will delete the selected material from Disk. Are you sure?"  # type: ignore
        ):
            return

        items = self.get_selected_items_from_thumblist()
        if not items:
            return
        for item in items:
            if not item:
                return

            asset_id = self.get_id_from_thumblist(item)
            self.library.remove_asset(asset_id)

        # Update View
        self.update_thumb_view()

    # Get the selected material from Library
    def get_selected_item_from_thumblist(self):
        """Return the material for the selected item in thumbview"""
        item = self.thumblist.selectedItems()[0]
        if not item:
            hou.ui.displayMessage("No material selected")  # type: ignore
            return None
        return item

    def get_selected_items_from_thumblist(
        self,
    ) -> list[QtWidgets.QListWidgetItem] | None:
        """Return the material for the selected item in thumbview"""
        items = self.thumblist.selectedItems()
        if not items:
            hou.ui.displayMessage("No material selected")  # type: ignore
            return None
        self.last_selected_items = items
        return items

    def get_selected_items_from_thumblist_silent(
        self,
    ) -> list[QtWidgets.QListWidgetItem] | None:
        """Return the material for the selected item in thumbview"""
        items = self.thumblist.selectedItems()
        if not items:
            return None
        self.last_selected_items = items
        return items

    #  Saves a material to the Library
    def save_asset(self) -> None:
        """Saves the selected nodes (Network Editor) to the Library"""
        # Get Selected from Network View
        sel = hou.selectedNodes()
        # Check selection
        if not sel:
            hou.ui.displayMessage("No material selected")  # type: ignore
            return
        if not self.library:
            hou.ui.displayMessage(
                "Please set a Materiallibrary first. Please use the MatLib Panel - Library/Open Dialog."  # type: ignore
            )  # type: ignore
            return
        self.get_material_info_user(sel)

    def get_material_info_user(self, sel: list[hou.Node]) -> None:
        """Query user for input upon material-save"""
        # Get Stuff from User
        dialog = usd_dialog.UsdDialog()
        r = dialog.exec_()

        if dialog.canceled or not r:
            return

        # Check if Category or Tags already exist
        if dialog.categories:
            self.library.check_add_category(dialog.categories)
        if dialog.tags:
            self.library.check_add_tags(dialog.tags)

        for asset in sel:
            self.library.add_asset(asset, dialog.categories, dialog.tags, dialog.fav)
        self.update_views()

    def import_assets(self) -> None:
        items = self.get_selected_items_from_thumblist()
        if not items:
            return
        for item in items:
            self.import_asset(item)

    #  Import material to Scene
    def import_asset(self, sel: QtWidgets.QListWidgetItem) -> None | hou.Node:
        """Import Material to scene"""
        if not sel:
            item = self.thumblist.selectedItems()[0]
        else:
            item = sel

        if not item:
            hou.ui.displayMessage("No Asset selected")  # type: ignore
            return

        asset_id = self.get_id_from_thumblist(item)

        return self.library.import_asset_to_scene(asset_id)

    def render_thumbnail(self, asset_id: str) -> None:
        # Move to correct context before rerendering assets
        if "MatX" in self.library.get_renderer_by_id(asset_id):
            self.library.context = hou.node("/stage")
        else:
            self.library.context = hou.node("/mat")

        builder = self.library.import_asset_to_scene(asset_id)
        if not builder:
            return
        self.library.create_thumbnail(builder, asset_id)

        if "stage" in self.library.context.path():
            builder.parent().destroy()
        else:
            builder.destroy()

    # Set IconSize via Slider
    def slide(self) -> None:
        self.library.thumbsize = self.click_slider.value()
        # Update Thumblist Grid
        self.thumblist.setIconSize(
            QtCore.QSize(self.library.thumbsize, self.library.thumbsize)
        )
        self.thumblist.setGridSize(
            QtCore.QSize(self.library.thumbsize + 10, self.library.thumbsize + 40)
        )

        self.update_views()
