import json
import hou
import os


class Prefs:
    def __init__(self) -> None:
        self.path: str = hou.getenv("EGMATLIB")
        self._directory = ""
        self.data = {}
        self.load()

    def save(self) -> None:
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

        with open(self.path + ("/settings.json"), "w", encoding="utf-8") as lib_json:
            json.dump(self.data, lib_json, indent=4)

    def load(self) -> None:
        with open(self.path + ("/settings.json"), encoding="utf-8") as lib_json:
            data = json.load(lib_json)
            self._directory = data["directory"]
            self._ext = data["extension"]
            self._img_ext = data["img_extension"]
            self.done_file = data["done_file"]
            self._img_dir = data["img_dir"]
            self._asset_dir = data["asset_dir"]

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

    def get_done_file(self) -> str:
        """Get Extension for done_file for singaling rendering process within houdini"""
        return self.done_file
