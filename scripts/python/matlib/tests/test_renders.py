import os, sys
import unittest
import hou

from scripts.python.matlib.tests import test_renders
from matlib.prefs import prefs
from matlib.core import category


class TestLib(unittest.TestCase):

    def test_load_houdini(self):
        print("Starting Tests")

        filepath = (
            hou.getenv("EGMATLIB")
            + "/scripts/python/matlib/tests/assets/houdini/Materials.hiplc"
        )
        hou.hipFile.load(filepath)

        self.assertEqual(1, 1, "Load Houdini  - Success!")

    def test_category(self):
        from matlib.core import category

        cat_model = category.Categories()
        cat_model.preferences.dir = (
            hou.getenv("EGMATLIB") + "/scripts/python/matlib/tests/assets/library"
        )
        cat_model.reload()
        count = cat_model.rowCount()

        self.assertEqual(count, 3, "Base Load Category Done! - Success!")

    def test_remove_category(self):

        cat_model = category.Categories()
        cat_model.preferences.dir = (
            hou.getenv("EGMATLIB") + "/scripts/python/matlib/tests/assets/library"
        )
        cat_model.reload()
        count = cat_model.rowCount()

        # Remove Category
        cat_model.remove_category("usds")
        count = cat_model.rowCount()
        self.assertEqual(count, 2, "Should be 2 Categories!")

    def test_add_category(self):

        cat_model = category.Categories()
        cat_model.preferences.dir = (
            hou.getenv("EGMATLIB") + "/scripts/python/matlib/tests/assets/library"
        )
        cat_model.reload()

        # Add Category
        cat_model.check_add_category("usds")
        count = cat_model.rowCount()
        self.assertEqual(count, 3, "Should be 3 Categories!")


if __name__ == "__main_":
    unittest.main()
