"""
Holds and loads the Preferences for the Matlib
"""

import os
import json
import hou


class Prefs:
    """
    Holds and loads the Preferences for the Matlib
    """

    def __init__(self) -> None:
        self.path: str = hou.getenv("EGMATLIB")
        self._directory = ""
        self.data = {}
        self.load()

    def save(self) -> None:
        """
        Sanitize and Save the Preferences to disk as json
        """
        # Sanitize Filepath
        if not self._directory.endswith("/"):
            self._directory = self._directory + "/"
        self._directory.replace("\\", "/")

        self.data["directory"] = self._directory
        self.data["extension"] = self._ext
        self.data["img_extension"] = self._img_ext
        self.data["done_file"] = self.done_file
        self.data["img_dir"] = self._img_dir
        self.data["asset_dir"] = self._asset_dir
        self.data["rendersize"] = self._rendersize
        self.data["thumbsize"] = self._thumbsize
        self.data["render_on_import"] = self._render_on_import
        self.data["renderer_materialx"] = self._renderer_matx_enabled
        self.data["renderer_mantra"] = self._renderer_mantra_enabled
        self.data["renderer_redshift"] = self._renderer_redshift_enabled
        self.data["renderer_octane"] = self._renderer_octane_enabled
        self.data["renderer_arnold"] = self._renderer_arnold_enabled

        with open(self.path + ("/settings.json"), "w", encoding="utf-8") as lib_json:
            json.dump(self.data, lib_json, indent=4)

    def load(self) -> None:
        """
        Load the Preferences from disk as json
        """
        with open(self.path + ("/settings.json"), encoding="utf-8") as lib_json:
            data = json.load(lib_json)
            self._directory = data["directory"]
            self._ext = data["extension"]
            self._img_ext = data["img_extension"]
            self.done_file = data["done_file"]
            self._img_dir = data["img_dir"]
            self._asset_dir = data["asset_dir"]
            self._rendersize = data["rendersize"]
            self._thumbsize = data["thumbsize"]
            self._render_on_import = data["render_on_import"]
            self._renderer_matx_enabled = data["renderer_materialx"]
            self._renderer_mantra_enabled = data["renderer_mantra"]
            self._renderer_redshift_enabled = data["renderer_redshift"]
            self._renderer_octane_enabled = data["renderer_octane"]
            self._renderer_arnold_enabled = data["renderer_arnold"]

            self.get_dir_from_user()

    def get_dir_from_user(self) -> None:
        """Get Directory from User and write into prefs"""
        count = 0
        while count < 3:
            if not os.path.exists(self.dir):
                hou.ui.displayMessage("Please choose a valid path")  # type: ignore
                path = hou.ui.selectFile(file_type=hou.fileType.Directory)
                self.dir = hou.expandString(path)
            else:
                return
            count += 1

    @property
    def dir(self) -> str:
        return self._directory

    @dir.setter
    def dir(self, val: str) -> None:
        self._directory = val

    @property
    def rendersize(self) -> int:
        return self._rendersize

    @rendersize.setter
    def rendersize(self, val: int) -> None:
        self._rendersize = val

    @property
    def thumbsize(self) -> int:
        return self._thumbsize

    @thumbsize.setter
    def thumbsize(self, val: int) -> None:
        self._thumbsize = val

    @property
    def render_on_import(self) -> int:
        return self._render_on_import

    @render_on_import.setter
    def render_on_import(self, val: int) -> None:
        self._render_on_import = val

    @property
    def img_dir(self) -> str:
        return self._img_dir

    @property
    def asset_dir(self) -> str:
        return self._asset_dir

    @property
    def img_ext(self) -> str:
        return self._img_ext

    @property
    def ext(self) -> str:
        return self._ext

    @property
    def renderer_matx_enabled(self) -> bool:
        return self._renderer_matx_enabled

    @renderer_matx_enabled.setter
    def renderer_matx_enabled(self, val: bool) -> None:
        self._renderer_matx_enabled = val

    @property
    def renderer_mantra_enabled(self) -> bool:
        return self._renderer_mantra_enabled

    @renderer_mantra_enabled.setter
    def renderer_mantra_enabled(self, val: bool) -> None:
        self._renderer_mantra_enabled = val

    @property
    def renderer_arnold_enabled(self) -> bool:
        return self._renderer_arnold_enabled

    @renderer_arnold_enabled.setter
    def renderer_arnold_enabled(self, val: bool) -> None:
        self._renderer_arnold_enabled = val

    @property
    def renderer_redshift_enabled(self) -> bool:
        return self._renderer_redshift_enabled

    @renderer_redshift_enabled.setter
    def renderer_redshift_enabled(self, val: bool) -> None:
        self._renderer_redshift_enabled = val

    @property
    def renderer_octane_enabled(self) -> bool:
        return self._renderer_octane_enabled

    @renderer_octane_enabled.setter
    def renderer_octane_enabled(self, val: bool) -> None:
        self._renderer_octane_enabled = val

    def get_done_file(self) -> str:
        """Get Extension for done_file for singaling rendering process within houdini"""
        return self.done_file
