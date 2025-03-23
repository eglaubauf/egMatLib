import json
import hou


###################################
########  THE USER PREFS ##########
###################################
class prefs:
    def __init__(self):
        self.path = hou.getenv("EGMATLIB")
        self.data = {}
        self.load()

    def save(self):
        self.data["directory"] = self.directory
        self.data["extension"] = self.ext
        self.data["img_extension"] = self.img_ext
        self.data["done_file"] = self.done_file
        self.data["img_dir"] = self.img_dir
        self.data["asset_dir"] = self.asset_dir

        with open(self.path + ("/settings.json"), "w") as lib_json:
            json.dump(self.data, lib_json, indent=4)

    def load(self):
        with open(self.path + ("/settings.json")) as lib_json:
            data = json.load(lib_json)
            self.directory = data["directory"]
            self.ext = data["extension"]
            self.img_ext = data["img_extension"]
            self.done_file = data["done_file"]
            self.img_dir = data["img_dir"]
            self.asset_dir = data["asset_dir"]
        return

    def get_dir(self):
        return self.directory

    def get_img_dir(self):
        return self.img_dir

    def get_asset_dir(self):
        return self.asset_dir

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

    # def get_usd_paths(self):
    #     return self.usd_paths
