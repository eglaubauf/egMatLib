import json
import hou


class prefs:
    def __init__(self) -> None:
        self.path: str = hou.getenv("EGMATLIB")
        self.show_buttons = False
        self.directory = ""
        self.data = {}
        self.load()

    def save(self) -> None:
        self.data["directory"] = self.directory
        self.data["extension"] = self.ext
        self.data["img_extension"] = self.img_ext
        self.data["done_file"] = self.done_file
        self.data["img_dir"] = self.img_dir
        self.data["asset_dir"] = self.asset_dir

        with open(self.path + ("/settings.json"), "w", encoding="utf-8") as lib_json:
            json.dump(self.data, lib_json, indent=4)

    def load(self) -> None:
        with open(self.path + ("/settings.json"), encoding="utf-8") as lib_json:
            data = json.load(lib_json)
            self.directory = data["directory"]
            self.ext = data["extension"]
            self.img_ext = data["img_extension"]
            self.done_file = data["done_file"]
            self.img_dir = data["img_dir"]
            self.asset_dir = data["asset_dir"]

    def get_dir(self) -> str:
        return self.directory

    def get_img_dir(self) -> str:
        return self.img_dir

    def get_asset_dir(self) -> str:
        return self.asset_dir

    def get_img_ext(self) -> str:
        return self.img_ext

    def get_ext(self) -> str:
        return self.ext

    def get_done_file(self) -> str:
        return self.done_file

    def get_btns(self) -> bool:
        return self.show_buttons

    def set_btns(self, val: bool) -> None:
        self.show_buttons = val

    def set_dir(self, val: str) -> None:
        self.directory = val
