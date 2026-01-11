"""
This Module holds the Model for the MaterialView/Thumbview for the MatlibPanel
"""

import os
import importlib
from typing import Any
from PySide6 import QtCore, QtGui

import hou

from matlib.core import material, database
from matlib.prefs import prefs
from matlib.render import thumbs, nodes

importlib.reload(material)
importlib.reload(database)
importlib.reload(nodes)
importlib.reload(thumbs)

favicon = hou.getenv("EGMATLIB") + "/scripts/python/matlib/res/def/Favorite.png"
missing = hou.getenv("EGMATLIB") + "/scripts/python/matlib/res/img/missing.jpg"
BASE_SIZE = 512


class ThumbnailWorker(QtCore.QThread):
    """
    Processes Thumbnails in a threaded Manner
    """

    thumbnail_ready = QtCore.Signal(int, QtGui.QImage)

    def __init__(self, items, size: int, parent: QtCore.QObject | None = None) -> None:
        super().__init__()
        self._items = items
        self._size = size

    def run(self) -> None:
        """Creates Thumbnails for previously passed items and emits signals when each image is created"""
        for data in self._items:

            img = QtGui.QImage(data[0]).scaled(QtCore.QSize(BASE_SIZE, BASE_SIZE))
            if img.isNull():
                continue
            if data[1]:
                fav_img = QtGui.QImage(favicon).scaled(
                    QtCore.QSize(BASE_SIZE, BASE_SIZE)
                )
                composite = QtGui.QImage(
                    QtCore.QSize(BASE_SIZE, BASE_SIZE), QtGui.QImage.Format_ARGB32
                )
                painter = QtGui.QPainter(composite)
                painter.drawImage(0, 0, img)
                painter.drawImage(0, 0, fav_img)
                painter.end()
                self.thumbnail_ready.emit(data[2], composite)
            else:
                self.thumbnail_ready.emit(data[2], img)


class MaterialLibrary(QtCore.QAbstractListModel):
    """The Model for the ThumbList View in the MatLibPanel
    Subclasses QtCore.QAbstractListModel
    """

    def __init__(self, parent: QtCore.QObject | None = None) -> None:
        super().__init__()

        self.preferences = prefs.Prefs()
        self.preferences.load()
        self._thumbsize = self.preferences.thumbsize

        db = database.DatabaseConnector()
        self._data = db.load(self.preferences.dir)

        self._assets = [material.Material.from_dict(d) for d in self._data["assets"]]
        self._tags = self._data["tags"]

        self._force_render = False  # Helper Var for Thumb Rendering

        self.IdRole = QtCore.Qt.ItemDataRole.UserRole  # 256
        self.CategoryRole = QtCore.Qt.ItemDataRole.UserRole + 1  # 257
        self.FavoriteRole = QtCore.Qt.ItemDataRole.UserRole + 2  # 258
        self.RendererRole = QtCore.Qt.ItemDataRole.UserRole + 3  # 259
        self.TagRole = QtCore.Qt.ItemDataRole.UserRole + 4  # 260
        self.DateRole = QtCore.Qt.ItemDataRole.UserRole + 5  # 261

        self.default_image = QtGui.QImage(missing).scaled(
            QtCore.QSize(BASE_SIZE, BASE_SIZE)
        )

        self.rebuild_thumbs()

        self._outofdate_thumb_list = []

    def _get__mat_paths(self):
        self._mat_paths = []
        for elem in range(self.rowCount()):
            mat_id = self._assets[elem].mat_id
            is_fav = self._assets[elem].fav
            path = (
                self.preferences.dir
                + self.preferences.img_dir
                + mat_id
                + self.preferences.img_ext
            )
            self._mat_paths.append((path, is_fav, elem))

    def switch_model_data(self):

        self.preferences.load()
        db = database.DatabaseConnector()
        self._data = db.reload_with_path(self.preferences.dir)
        self._thumbsize = self.preferences.thumbsize

        self._assets = [material.Material.from_dict(d) for d in self._data["assets"]]
        self._tags = self._data["tags"]
        self.rebuild_thumbs()

    def flags(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex
    ) -> QtCore.Qt.ItemFlag:
        default = super().flags(index)
        return default | QtCore.Qt.ItemFlag.ItemIsDragEnabled

    def rebuild_thumbs(self):
        self._thumbs = [0 for x in range(self.rowCount())]
        self._mat_paths = []
        self._get__mat_paths()
        self._start_worker()

    def update_outofdate_thumb_list(self):
        paths = []
        for curr_index in self._outofdate_thumb_list:
            mat_id = self._assets[curr_index.row()].mat_id
            for elem in range(self.rowCount()):
                if mat_id == self._assets[elem].mat_id:
                    is_fav = self._assets[elem].fav
                    path = (
                        self.preferences.dir
                        + self.preferences.img_dir
                        + mat_id
                        + self.preferences.img_ext
                    )

                    paths.append((path, is_fav, curr_index.row()))

        self._start_worker(paths)
        self._outofdate_thumb_list.clear()

    def _add_thumb_paths(self, index: QtCore.QModelIndex):
        mat_id = self._assets[index.row()].mat_id

        paths = []
        for elem in range(self.rowCount()):
            if mat_id == self._assets[elem].mat_id:
                is_fav = self._assets[elem].fav
                path = (
                    self.preferences.dir
                    + self.preferences.img_dir
                    + mat_id
                    + self.preferences.img_ext
                )

                paths.append((path, is_fav, index.row()))
        # Extend Thumbslist by 1 and fill later
        self._thumbs.append(0)
        if self.preferences.render_on_import or self._force_render:
            self._start_worker(paths)

    def _remove_thumb(self, elem):
        self._thumbs.pop(elem)

    def _start_worker(self, paths=None):
        if not paths:
            paths = self._mat_paths
        items = paths

        self.worker = ThumbnailWorker(items, self._thumbsize)
        self.worker.thumbnail_ready.connect(self._on_thumb_ready)
        self.worker.start()

    @QtCore.Slot(int, QtGui.QImage)
    def _on_thumb_ready(self, elem, image):
        self._thumbs[elem] = image
        self.dataChanged.emit(
            self.index(elem), self.index(elem), QtCore.Qt.ItemDataRole.DecorationRole
        )

    def set_custom_iconsize(self, size: QtCore.QSize) -> None:
        """Sets a custom IconSize - usually called via the View - Thumbnail Size Slider"""
        self.default_image = QtGui.QImage(missing).scaled(size)
        self._thumbsize = size.width()

    def rowCount(
        self, parent: QtCore.QModelIndex | QtCore.QPersistentModelIndex | None = None
    ) -> int:
        return len(self._assets)

    def data(
        self, index: QtCore.QModelIndex | QtCore.QPersistentModelIndex, role: int = 0
    ) -> Any:
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._assets[index.row()].name

        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            image = self._thumbs[index.row()]
            if image:
                return image.scaled(QtCore.QSize(self._thumbsize, self._thumbsize))
            return self.default_image

        if role == self.CategoryRole:
            return self._assets[index.row()].categories

        if role == self.TagRole:
            return self._assets[index.row()].tags

        if role == self.FavoriteRole:
            return self._assets[index.row()].fav

        if role == self.RendererRole:
            return str(self._assets[index.row()].renderer)

        if role == self.DateRole:
            return str(self._assets[index.row()].date)

        if role == self.IdRole:
            return str(self._assets[index.row()].mat_id)

    def save(self) -> None:
        """Save data to disk as json"""
        db = database.DatabaseConnector()
        data = {}
        data["tags"] = self._tags
        data["assets"] = [asset.get_as_dict() for asset in self._assets]
        db.set(data)
        db.save()

    @property
    def assets(self) -> list:
        """
        Docstring for assets

        :param self: Description
        :return: Description
        :rtype: list[Any]
        """
        return self._assets

    @property
    def tags(self) -> list:
        """
        Docstring for tags

        :param self: Description
        :return: Description
        :rtype: list[Any]
        """
        return self._tags

    @property
    def thumbsize(self) -> int:
        """
        Docstring for thumbsize

        :param self: Description
        :return: Description
        :rtype: int
        """
        return self._thumbsize

    @thumbsize.setter
    def thumbsize(self, val: int) -> None:
        self._thumbsize = val

    def sanitize_tags(self, tags):
        ts = []
        for t in tags.split(","):
            t = t.replace(" ", "")
            ts.append(t)

        ts = set(ts)
        new_tags = ",".join(ts)
        return new_tags

    def set_assetdata(self, index: QtCore.QModelIndex, name, cats, tags, fav) -> None:
        """Set Assetdata for the given index and parameters
        the library is saved immidiately after"""
        tags = self.sanitize_tags(tags)
        self.check_add_tags(tags)

        asset = self._assets[index.row()]

        name = name if name != "Multiple Values..." else asset.name
        cats = cats if cats != "Multiple Values..." else asset.categories
        tags = tags if tags != "Multiple Values..." else asset.tags

        asset.set_data(name, cats, tags, fav, None)
        self._outofdate_thumb_list.append(index)
        self.save()

    def remove_asset(self, index: QtCore.QModelIndex) -> None:
        """Removes a material from this Library and Disk
        the library is saved immediately after"""

        if len(self._assets) < index.row() + 1:
            return
        asset = self._assets[index.row()]

        # Remove Files from Disk

        asset_file_path = os.path.join(
            self.preferences.dir,
            self.preferences.asset_dir,
            asset.mat_id + self.preferences.ext,
        )
        img_file_path = os.path.join(
            self.preferences.dir,
            self.preferences.img_dir,
            asset.mat_id + self.preferences.img_ext,
        )
        interface_file_path = os.path.join(
            self.preferences.dir,
            self.preferences.asset_dir,
            asset.mat_id + ".interface",
        )

        if os.path.exists(asset_file_path):
            os.remove(asset_file_path)
        if os.path.exists(img_file_path):
            os.remove(img_file_path)
        if os.path.exists(interface_file_path):
            os.remove(interface_file_path)

        self._assets.remove(asset)
        self._remove_thumb(index.row())

        self.save()

    def check_add_tags(self, tag: str) -> None:
        """Checks if this tag exists and adds it if needed"""
        for t in tag.split(","):
            t = t.replace(" ", "")
            if t != "" and t not in self.tags:
                self.tags.append(t)
        self.save()

    def get_current_network_node(self) -> None | hou.Node:
        """Return thre current Node in the Network Editor"""
        for pt in hou.ui.paneTabs():  # type: ignore
            if pt.type() == hou.paneTabType.NetworkEditor:
                return pt.currentNode()
        return None

    def remove_category(self, cat: str) -> None:
        """Removes the given category from the library (and also in all assets)"""
        # check assets against category and remove there also:
        for asset in self._assets:
            asset.remove_category(cat)

    def rename_category(self, old: str, new: str) -> None:
        """Renames the given category in the library (and also in all assets)"""
        # Update all Categories with that name in all assets
        for asset in self._assets:
            asset.rename_category(old, new)

    def add_asset(self, node: hou.Node, cats: str, tags: str, fav: bool) -> None:
        """Add a Material to this Library"""
        handler = nodes.NodeHandler(self.preferences)
        renderer = handler.get_renderer_from_node(node)
        new_mat = material.Material()
        tags = self.sanitize_tags(tags)
        new_mat.set_data(node.name(), cats, tags, fav, renderer)

        if handler.save_node(node, new_mat.mat_id, False):
            self._assets.append(new_mat)
            self._add_thumb_paths(self.index(self.rowCount() - 1, 0))
            self.save()

    def add_asset_from_strings(
        self, name: str, cats: str, tags: str, fav: bool, renderer: str
    ):
        """Append an assset from Strings only - the user has to take care of copying files on disk"""
        new_asset = material.Material()
        tags = self.sanitize_tags(tags)
        new_asset.set_data(
            name,
            cats,
            tags,
            fav,
            renderer,
        )
        self._assets.append(new_asset)
        # self._add_thumb_paths(self.index(self.rowCount() - 1, 0))
        # self.save()
        return self._assets[self.rowCount() - 1]

    def cleanup_db(self) -> None:
        """Removes orphan data from disk and highlights missing thumbnails"""
        mark_rmv = 0
        mark_render = 0

        for row, asset in enumerate(self._assets):
            interface_path = os.path.join(
                self.preferences.dir,
                self.preferences.asset_dir,
                str(asset.mat_id) + ".interface",
            )
            mat_path = os.path.join(
                self.preferences.dir,
                self.preferences.asset_dir,
                str(asset.mat_id) + ".mat",
            )
            img_path = os.path.join(
                self.preferences.dir,
                self.preferences.img_dir,
                str(asset.mat_id) + self.preferences.img_ext,
            )

            if not os.path.exists(interface_path) or not os.path.exists(mat_path):
                print("Asset %d missing on disk -> Removed from disk!", asset.mat_id)
                mark_rmv = 1
                self.remove_asset(self.index(row))
            if not os.path.exists(img_path):
                mark_render = 1
                print(
                    f"Image for Asset { asset.mat_id} missing on disk -> Needs Rendering!"
                )

        mats_path = os.path.join(self.preferences.dir, self.preferences.asset_dir)
        mark_lone = 0
        for f in os.listdir(mats_path):
            if f.endswith(".mat") or f.endswith(".interface"):
                split = f.split(".")[0]
                found = [mat for mat in self._assets if str(split) in str(mat.mat_id)]
                if not found:
                    print(
                        f"Lonely File at {os.path.join(mats_path, f)} found -> Removed from disk!"
                    )
                    try:
                        os.remove(os.path.join(mats_path, f))
                        mark_lone = 1
                    except OSError:
                        pass

        mats_path = os.path.join(self.preferences.dir, self.preferences.img_dir)
        for f in os.listdir(mats_path):
            if f.endswith(".png"):
                split = f.split(".")[0]
                found = [mat for mat in self._assets if str(split) in str(mat.mat_id)]
                if not found:
                    print(
                        f"Lonely File at {os.path.join(mats_path, f)} found. Removing from disk"
                    )
                    try:
                        os.remove(os.path.join(mats_path, f))
                        mark_lone = 1
                    except OSError:
                        pass

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

    def toggle_fav(self, index: QtCore.QModelIndex) -> None:
        """
        Toggle the Favorite Parameter for the given QModelIndex

        :param self: Description
        :param index: Description
        :type index: QtCore.QModelIndex
        """
        self._assets[index.row()].fav = False if self._assets[index.row()].fav else True
        self.save()
        self._outofdate_thumb_list.append(index)
        self.update_outofdate_thumb_list()

    def render_thumbnail(self, index: QtCore.QModelIndex) -> None:
        """
        Render the Thumbnail for the given QModelIndex

        :param self: Description
        :param index: Description
        :type index: QtCore.QModelIndex
        """
        self._force_render = True
        renderer = thumbs.ThumbNailRenderer(self.preferences, self._assets[index.row()])
        renderer.create_thumbnail()
        self._add_thumb_paths(index)
        self._force_render = False

    def import_asset_to_scene(self, index: QtCore.QModelIndex) -> None:
        """
        Import the given QModelIndex to the current Houdini Scene/Network Editor

        :param self: Description
        :param index: Description
        :type index: QtCore.QModelIndex
        """
        importer = nodes.NodeHandler(self.preferences)
        importer.import_asset_to_scene(self._assets[index.row()])
