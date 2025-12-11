import os
import shutil
import sys
import subprocess
import importlib
from PySide6 import QtWidgets, QtGui, QtCore, QtUiTools

from matlib.core import library
from matlib.core import category
import hou

from matlib.core import multifilterproxy_model
from matlib.dialogs import (
    about_dialog,
    material_dialog,
    prefs_dialog,
    usd_dialog,
)
from matlib.prefs import prefs
from matlib.helpers import ui_helpers

importlib.reload(library)
importlib.reload(category)
importlib.reload(prefs)
importlib.reload(ui_helpers)

importlib.reload(material_dialog)
importlib.reload(about_dialog)
importlib.reload(prefs_dialog)
importlib.reload(usd_dialog)


class MatLibPanel(QtWidgets.QWidget):
    def __init__(self) -> None:
        super(MatLibPanel, self).__init__()

        # Initialize
        self.script_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        self.material_model = None
        self.selected_cat = None

        # Attach models to views
        self.category_model = category.Categories()
        self.category_sorted_model = QtCore.QSortFilterProxyModel()
        self.category_sorted_model.setSourceModel(self.category_model)
        self.category_sorted_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.category_sorted_model.sort(0)

        self.material_model = library.MaterialLibrary()
        self.material_sorted_model = multifilterproxy_model.MultiFilterProxyModel()
        self.material_sorted_model.setSourceModel(self.material_model)
        self.material_sorted_model.setSortCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.material_sorted_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.material_sorted_model.sort(0)
        self.material_sorted_model.setDynamicSortFilter(False)  # Improves Performance
        self.material_selection_model = QtCore.QItemSelectionModel(
            self.material_sorted_model
        )
        self.init_ui()

        # Attach Models
        self.cat_list.setModel(self.category_sorted_model)
        self.thumblist.setModel(self.material_sorted_model)
        self.thumblist.setSelectionModel(self.material_selection_model)

        self.material_selection_model.selectionChanged.connect(self.update_details_view)
        self.filter_renderer()
        self.slide()

        # Load prefs and open library
        self.prefs = prefs.Prefs()
        self.load()

    def open(self) -> None:
        self.material_model.save()
        self.material_model = library.MaterialLibrary()
        self.prefs.load()
        self.load()
        hou.ui.displayMessage("Library Reloaded successfully!")

    def load(self) -> None:
        new_folder = False
        if not os.path.exists(self.prefs.dir + "/library.json"):
            oldpath = (
                hou.getenv("EGMATLIB") + "/scripts/python/matlib/res/def/library.json"
            )
            shutil.copy(oldpath, self.prefs.dir + "/library.json")
            new_folder = True
        if not os.path.exists(self.prefs.dir + self.prefs.img_dir):
            os.mkdir(self.prefs.dir + self.prefs.img_dir)
            os.mkdir(self.prefs.dir + self.prefs.asset_dir)
            new_folder = True
        if new_folder:
            msg = "A new library has been created successfully"
            hou.ui.displayMessage(msg)  # type: ignore

    def toggle_catview(self) -> None:
        if self.action_catview.isChecked():
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

    def init_ui(self) -> None:
        """Creates the panel-view on load"""
        # Load UI from ui.file
        loader = QtUiTools.QUiLoader()
        file = QtCore.QFile(self.script_path + "/ui/matlib.ui")
        file.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(file)
        file.close()

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

        self.action_force_update = self.ui.findChild(
            QtGui.QAction, "action_force_update"
        )

        self.thumblist = self.ui.findChild(QtWidgets.QListView, "thumbview")
        self.thumblist.doubleClicked.connect(self.import_asset)
        self.thumblist.clicked.connect(self.update_details_view)

        # Category UI
        self.cat_list = self.ui.findChild(QtWidgets.QListView, "catview")
        self.cat_list.clicked.connect(self.update_selected_cat)

        self.line_filter = self.ui.findChild(QtWidgets.QLineEdit, "line_filter")
        self.line_filter.textEdited.connect(self.filter_thumb_view)
        # Updated Details UI
        self.details = self.ui.findChild(QtWidgets.QTableWidget, "details_widget")
        self.line_name = self.ui.findChild(QtWidgets.QLineEdit, "line_name")
        self.line_cat = self.ui.findChild(QtWidgets.QLineEdit, "line_cat")
        self.line_tags = self.ui.findChild(QtWidgets.QLineEdit, "line_tags")
        self.line_id = self.ui.findChild(QtWidgets.QLineEdit, "line_id")
        self.line_id.setDisabled(True)

        self.line_date = self.ui.findChild(QtWidgets.QLineEdit, "line_date")
        self.line_date.setDisabled(True)

        self.box_fav = self.ui.findChild(QtWidgets.QCheckBox, "cb_set_fav")
        self.btn_update = self.ui.findChild(QtWidgets.QPushButton, "btn_update")
        self.btn_update.clicked.connect(self.user_update_asset)

        # Options
        self.cb_favsonly = self.ui.findChild(QtWidgets.QCheckBox, "cb_FavsOnly")
        self.cb_favsonly.stateChanged.connect(self.filter_favs)

        # Material
        self.cb_redshift = self.ui.findChild(QtWidgets.QRadioButton, "cb_Redshift")
        self.cb_mantra = self.ui.findChild(QtWidgets.QRadioButton, "cb_Mantra")
        self.cb_arnold = self.ui.findChild(QtWidgets.QRadioButton, "cb_Arnold")
        self.cb_octane = self.ui.findChild(QtWidgets.QRadioButton, "cb_Octane")
        self.cb_matx = self.ui.findChild(QtWidgets.QRadioButton, "cb_MatX")

        self.cb_showcat = self.ui.findChild(QtWidgets.QCheckBox, "cb_showCat")

        self.cb_redshift.toggled.connect(self.filter_renderer)
        self.cb_mantra.toggled.connect(self.filter_renderer)
        self.cb_arnold.toggled.connect(self.filter_renderer)
        self.cb_octane.toggled.connect(self.filter_renderer)
        self.cb_matx.toggled.connect(self.filter_renderer)

        # IconSize Slider
        self.slide_iconsize = self.ui.findChild(QtWidgets.QSlider, "slide_iconSize")
        self.slide_iconsize.setRange(32, 512)
        self.slide_iconsize.setValue(128)
        self.slide_iconsize.setVisible(False)

        # Set Up Clickable Slider
        self.click_slider = ui_helpers.ClickSlider()
        self.click_slider.setOrientation(QtCore.Qt.Horizontal)
        self.click_slider.setRange(32, 256)
        self.click_slider.setValue(128)
        self.click_slider.setSingleStep(50)
        self.click_slider.setPageStep(50)
        self.slider_layout = self.ui.findChild(QtWidgets.QVBoxLayout, "slider_layout")
        self.slider_layout.addWidget(self.click_slider)
        self.click_slider.valueChanged.connect(self.slide)

        # RC Menus
        self.thumblist.customContextMenuRequested.connect(self.thumblist_rc_menu)
        self.cat_list.customContextMenuRequested.connect(self.catlist_rc_menu)

        self.a_folder = self.ui.findChild(QtGui.QAction, "action_import_folder")
        self.a_folder.setDisabled(True)
        self.a_folder.setVisible(False)

        self.a_files = self.ui.findChild(QtGui.QAction, "action_import_files")
        self.a_files.setDisabled(True)
        self.a_files.setVisible(False)

        # Import Group Disable
        self.import_group = self.ui.findChild(QtWidgets.QGroupBox, "import_group")
        self.import_group.setDisabled(True)
        self.import_group.setVisible(False)

        # set main layout and attach to widget
        mainlayout = QtWidgets.QVBoxLayout()
        mainlayout.addWidget(self.ui)
        mainlayout.setContentsMargins(0, 0, 0, 0)  # Remove Margins

        self.setLayout(mainlayout)

        # Cleanup UI
        self.setStyleSheet("""  font-family: Lato; """)
        self.menu.setStyleSheet(""" font-family: Lato; """)
        self.menuGoto.setStyleSheet("""  font-family: Lato; """)

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
        action = cmenu.exec_(QtGui.QCursor.pos())

        if action == action_delete:
            self.delete_asset()
        elif action == action_render:
            self.update_single_asset()
        elif action == action_import:
            self.import_asset()
        elif action == action_renderall:
            self.update_all_assets()
        elif action == action_thumb_viewport:
            self.update_single_asset()
        elif action == action_toggle_fav:
            self.toggle_fav()

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
        self.material_model.layoutAboutToBeChanged.emit()
        indexes = self.material_selection_model.selectedIndexes()
        for index in indexes:
            idx = self.material_sorted_model.mapToSource(index)
            self.material_model.toggle_fav(idx)
        self.material_model.layoutChanged.emit()
        self.update_details_view()

    # User Stuff
    def show_about(self) -> None:
        about = about_dialog.AboutDialog()
        about.exec_()

    def show_prefs(self) -> None:
        if not self.material_model:
            hou.ui.displayMessage("Please open a library first")  # type: ignore
            return
        prefs = prefs_dialog.PrefsDialog(self.prefs)
        prefs.exec_()

        if prefs.canceled:
            return

        # Update Thumblist Grid
        self.thumblist.setIconSize(
            QtCore.QSize(self.material_model.thumbsize, self.material_model.thumbsize)
        )
        self.thumblist.setGridSize(
            QtCore.QSize(
                self.material_model.thumbsize + 10, self.material_model.thumbsize + 40
            )
        )

    def cleanup_db(self) -> None:
        if not self.material_model:
            hou.ui.displayMessage("Please open a library first")  # type: ignore
            return
        self.material_model.cleanup_db()

    def open_usdlib_folder(self) -> None:
        if not self.material_model:
            hou.ui.displayMessage("Please open a library first")  # type: ignore
            return
        lib_dir = self.material_model.path
        lib_dir.encode("unicode_escape")

        if sys.platform == "linux" and sys.platform == "linux2":  # Linux
            os.startfile(lib_dir)
            return
        elif sys.platform == "darwin":  # MacOS
            opener = "open"
            subprocess.call([opener, lib_dir])
        elif sys.platform == "win32":  # MacOS:  # Windows
            os.startfile(lib_dir)

    def add_category_user(self) -> None:
        choice, cat = hou.ui.readInput("Please enter the new category name:")  # type: ignore
        if choice:  # Return if no
            return

        self.material_model.layoutAboutToBeChanged.emit()
        self.category_model.layoutAboutToBeChanged.emit()

        self.material_model.check_add_category(cat)

        self.material_model.layoutChanged.emit()
        self.category_model.layoutChanged.emit()

    def rmv_category_user(self) -> None:
        """Removes a category - called by user change in UI"""
        # Prevent Deletion of "All" - Category
        self.material_model.layoutAboutToBeChanged.emit()
        self.category_model.layoutAboutToBeChanged.emit()
        for index in self.cat_list.selectedIndexes():
            if index.data(QtCore.Qt.ItemDataRole.DisplayRole) == "All":
                return
            self.material_model.remove_category(
                index.data(QtCore.Qt.ItemDataRole.DisplayRole)
            )

        self.material_model.save()
        self.material_model.layoutChanged.emit()
        self.category_model.layoutChanged.emit()

    def rename_category_user(self) -> None:
        """Renames a category - called by user change in UI"""
        choice, cat = hou.ui.readInput("Please enter the new category name:")  # type: ignore
        if choice:  # Return if no
            return

        self.material_model.layoutAboutToBeChanged.emit()
        self.category_model.layoutAboutToBeChanged.emit()
        for index in self.cat_list.selectedIndexes():
            if index.data(QtCore.Qt.ItemDataRole.DisplayRole) == "All":
                return

            self.material_model.rename_category(
                index.data(QtCore.Qt.ItemDataRole.DisplayRole), cat
            )

        self.material_model.save()
        self.material_model.layoutChanged.emit()
        self.category_model.layoutChanged.emit()

    def filter_thumb_view(self) -> None:
        """Get Filter from user and trigger view update"""
        # self.material_sorted_model.setFilterRole(0)
        self.material_sorted_model.setFilter(
            QtCore.Qt.ItemDataRole.DisplayRole, self.line_filter.text()
        )
        self.material_sorted_model.sort(0)

    def filter_favs(self) -> None:
        """Get Filter from user and trigger view update"""
        filter = (
            True
            if self.cb_favsonly.checkState() == QtCore.Qt.CheckState.Checked
            else ""
        )

        self.material_sorted_model.setFilter(self.material_model.FavoriteRole, filter)
        self.material_sorted_model.sort(0)

    def filter_renderer(self) -> None:
        """Get Filter from user and trigger view update"""
        filter = self.cb_matx.group().checkedButton().text()
        self.material_sorted_model.setFilter(self.material_model.RendererRole, filter)
        self.material_sorted_model.sort(0)

    def user_update_asset(self) -> None:
        indexes = self.material_selection_model.selectedIndexes()
        self.material_model.layoutAboutToBeChanged.emit()
        self.category_model.layoutAboutToBeChanged.emit()
        for index in indexes:
            idx = self.material_model.index(
                self.material_sorted_model.mapToSource(index).row()
            )
            name = self.line_name.text()
            tags = self.line_tags.text()
            cats = self.line_cat.text()
            fav = self.box_fav.isChecked()
            self.material_model.set_assetdata(idx, name, cats, tags, fav)

        self.material_model.layoutChanged.emit()
        self.category_model.layoutChanged.emit()

    def update_details_view(self) -> None:
        """Update upon changes in Detail view"""
        if not self.material_selection_model.hasSelection():
            self.line_name.setText("")
            self.line_id.setText("")
            self.line_date.setText("")
            self.line_tags.setText("")
            self.line_cat.setText("")
            self.box_fav.setCheckState(QtCore.Qt.CheckState.Unchecked)
            return

        indexes = self.material_selection_model.selectedIndexes()
        asset_id = ""
        name = ""
        date = ""
        sel_cats = []
        sel_tags = []
        fav = []
        for idx in indexes:
            curr_asset = self.material_model.index(
                self.material_sorted_model.mapToSource(idx).row()
            )
            name = curr_asset.data(QtCore.Qt.ItemDataRole.DisplayRole)
            asset_id = curr_asset.data(self.material_model.IdRole)
            date = curr_asset.data(self.material_model.DateRole)

            for cat in curr_asset.data(self.material_model.CategoryRole):
                sel_cats.append(cat)
            for tag in curr_asset.data(self.material_model.TagRole):
                sel_tags.append(tag)
            fav.append(curr_asset.data(self.material_model.FavoriteRole))

        msg = "Multiple Values..." if len(indexes) > 1 else name
        self.line_name.setText(msg)

        msg = "Multiple Values..." if len(indexes) > 1 else asset_id
        self.line_id.setText(msg)

        msg = "Multiple Values..." if len(indexes) > 1 else date
        self.line_date.setText(msg)

        msg = (
            QtCore.Qt.CheckState.Checked
            if fav[0] is True
            else QtCore.Qt.CheckState.Unchecked
        )
        msg = QtCore.Qt.CheckState.PartiallyChecked if len(indexes) > 1 else msg
        self.box_fav.setCheckState(msg)

        msg = (
            sel_cats[0]
            if len(sel_cats) < 2
            else ", ".join(list(filter(None, set(sel_cats))))
        )
        self.line_cat.setText(msg)

        msg = (
            sel_tags[0]
            if len(sel_cats) < 2
            else ", ".join(list(filter(None, set(sel_tags))))
        )
        self.line_tags.setText(msg)

    # Update the Views when selection changes
    def update_selected_cat(self) -> None:
        """Update thumb view on change of category"""
        index = self.cat_list.selectedIndexes()[0]
        if index.data() == "All":
            self.material_sorted_model.setFilter(self.material_model.CategoryRole, "")
        else:
            self.material_sorted_model.setFilter(
                self.material_model.CategoryRole, index.data()
            )

    # Library Stuffs
    def update_all_assets(self) -> None:
        """Rerenders all assets in the library - The UI is blocked for the duration of the render"""
        if not self.material_model:
            hou.ui.displayMessage("Please open a library first")  # type: ignore
            return

        if not hou.ui.displayConfirmation(
            """This can take a long time to render. Houdini will not be responsive during that time.
            Do you want continue rendering all visible assets?"""  # type: ignore
        ):  # type: ignore
            return
        self.material_model.layoutAboutToBeChanged.emit()
        for i in range(self.material_model.rowCount()):
            self.material_model.render_thumbnail(self.material_model.index(i))
        self.material_model.layoutChanged.emit()
        hou.ui.displayMessage("Updating all Thumbnails finished")  # type: ignore

    # Rerender Selected Asset
    def update_single_asset(self) -> None:
        """Rerenders a single Asset in the library - The UI is blocked for the duration of the render"""
        indexes = self.material_selection_model.selectedIndexes()
        self.material_model.layoutAboutToBeChanged.emit()
        for index in indexes:
            idx = self.material_sorted_model.mapToSource(index)
            self.material_model.render_thumbnail(idx)
        self.material_model.layoutChanged.emit()
        hou.ui.displayMessage("Thumbnail(s) updated")  # type: ignore

    def delete_asset(self) -> None:
        """Deletes the selected material from Disk and Library"""
        if not hou.ui.displayConfirmation(
            "This will delete the selected material(s) from Disk. Are you sure?"  # type: ignore
        ):
            return

        indexes = self.material_selection_model.selectedIndexes()
        self.material_model.layoutAboutToBeChanged.emit()
        for index in indexes:
            idx = self.material_sorted_model.mapToSource(index)
            self.material_model.remove_asset(idx)

        self.material_model.layoutChanged.emit()

    #  Saves a material to the Library
    def save_asset(self) -> None:
        """Saves the selected nodes (Network Editor) to the Library"""
        # Get Selected from Network View
        sel = hou.selectedNodes()
        # Check selection
        if not sel:
            hou.ui.displayMessage("No material selected")  # type: ignore
            return
        if not self.material_model:
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
            self.material_model.check_add_category(dialog.categories)
        if dialog.tags:
            self.material_model.check_add_tags(dialog.tags)

        self.material_model.layoutAboutToBeChanged.emit()
        self.category_model.layoutAboutToBeChanged.emit()
        for asset in sel:
            self.material_model.add_asset(
                asset, dialog.categories, dialog.tags, dialog.fav
            )
        self.material_model.layoutChanged.emit()
        self.category_model.layoutChanged.emit()

    def import_asset(self):
        """Import Material to scene"""
        for index in self.thumblist.selectedIndexes():

            self.material_model.import_asset_to_scene(
                self.material_sorted_model.mapToSource(index)
            )

    # Set IconSize via Slider
    def slide(self) -> None:

        self.material_model.thumbsize = self.click_slider.value()
        # Update Thumblist Grid

        self.thumblist.setGridSize(
            QtCore.QSize(
                self.material_model.thumbsize + 10, self.material_model.thumbsize + 40
            )
        )
        self.thumblist.setIconSize(
            QtCore.QSize(self.material_model.thumbsize, self.material_model.thumbsize)
        )
        # Also need to resize the images!
        self.material_model.setCustomIconSize(
            QtCore.QSize(self.material_model.thumbsize, self.material_model.thumbsize)
        )
