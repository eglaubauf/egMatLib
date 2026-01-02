import os
import json
import importlib
import shutil

import hou

from matlib.core import material, library
from matlib.prefs import prefs

importlib.reload(material)


class LibraryUpgrader:

    def __init__(
        self, path, materialmodel: library.MaterialLibrary, preferences: prefs.Prefs
    ):

        self._data = {}
        self._path = path
        self._materialmodel = materialmodel
        self._prefs = preferences

        # Load json from disk
        self.load()

        self._source_img_dir = os.path.dirname(path) + "/img/"
        self._source_asset_dir = os.path.dirname(path) + "/mat/"
        self._source_img_ext = ".png"

        self._dest_img_dir = self._prefs.dir + self._prefs.img_dir
        self._dest_asset_dir = self._prefs.dir + self._prefs.asset_dir
        self._dest_img_ext = self._prefs.img_ext

        self._interface_ext = ".interface"
        self._node_ext = ".mat"

        self._assets = [material.Material.from_dict(d) for d in self._data["assets"]]
        self._categories = self._data["categories"]
        self._tags = self._data["tags"]

    def load(self) -> dict:
        """
        Loads the old Database from disk as json
        """
        if not self._data:
            with open(self._path, encoding="utf_8") as lib_json:
                self._data = json.load(lib_json)
        return self._data

    def upgrade_v1_to_v2(self):
        """
        Upgrade selected json file to version 2 of MatLib

        :param self: Description
        """
        self._materialmodel.layoutAboutToBeChanged.emit()
        for curr_asset in self._assets:

            if "-1" in str(curr_asset.mat_id):
                continue

            cats = ",".join(curr_asset.categories)
            tags = ",".join(curr_asset.tags)
            renderer = curr_asset.renderer
            if "matx" in curr_asset.renderer.lower():
                renderer = "MaterialX"

            new_asset = self._materialmodel.add_asset_from_strings(
                curr_asset.name,
                cats,
                tags,
                curr_asset.fav,
                renderer,
            )

            try:
                self._copy_files(curr_asset, new_asset)
            except OSError:
                hou.ui.displayMessage(
                    "On Error occured during copying. Please check files"
                )

        self._materialmodel.save()
        self._materialmodel.rebuild_thumbs()
        self._materialmodel.layoutChanged.emit()

    def _copy_files(self, curr_asset: material.Material, new_asset: material.Material):
        """
        Copy files from Source to Target Directory

        :param self: Description
        :param curr_asset: Material in Old Library
        :type curr_asset: material.Material
        :param new_asset: Newly Generated Material
        :type new_asset: material.Material
        """
        # Copy Image
        source_img_file = (
            self._source_img_dir + str(curr_asset.mat_id) + self._source_img_ext
        )
        dest_img_file = self._dest_img_dir + new_asset.mat_id + self._dest_img_ext
        # Copy Asset
        source_interface_file = (
            self._source_asset_dir + str(curr_asset.mat_id) + self._interface_ext
        )
        dest_interface_file = (
            self._dest_asset_dir + new_asset.mat_id + self._interface_ext
        )

        # Copy Asset
        source_node_file = (
            self._source_asset_dir + str(curr_asset.mat_id) + self._node_ext
        )
        dest_node_file = self._dest_asset_dir + new_asset.mat_id + self._node_ext
        print(f"---------------------")
        print(f"MatLibUpgrader: Copy {source_img_file} to {dest_img_file}")
        shutil.copy(source_img_file, dest_img_file)
        print(f"MatLibUpgrader: Copy {source_interface_file} to {dest_interface_file}")
        shutil.copy(source_interface_file, dest_interface_file)
        print(f"MatLibUpgrader: Copy {source_node_file} to {dest_node_file}")
        shutil.copy(source_node_file, dest_node_file)
        print(f"---------------------")
