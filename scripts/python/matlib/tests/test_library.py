"""
Unit tests for library.py

This module contains comprehensive unit tests for the MaterialLibrary and ThumbnailWorker classes.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import sys
from typing import Any
from matlib.core import library

from PySide6 import QtCore, QtGui


class TestMaterialLibrary(unittest.TestCase):
    """Test suite for MaterialLibrary class"""

    def setUp(self):
        """Set up test fixtures before each test"""
        self.mock_prefs = Mock()
        self.mock_prefs.thumbsize = 256
        self.mock_prefs.dir = "/test/dir/"
        self.mock_prefs.img_dir = "img"
        self.mock_prefs.img_ext = ".png"
        self.mock_prefs.asset_dir = "assets"
        self.mock_prefs.ext = ".mat"
        self.mock_prefs.render_on_import = False

        self.mock_db = Mock()
        self.mock_data = {
            "assets": [
                {
                    "mat_id": "mat1",
                    "name": "Material 1",
                    "fav": False,
                    "categories": ["cat1"],
                    "tags": ["tag1"],
                    "renderer": "mantra",
                    "date": "2026-01-01",
                },
                {
                    "mat_id": "mat2",
                    "name": "Material 2",
                    "fav": True,
                    "categories": ["cat2"],
                    "tags": ["tag2"],
                    "renderer": "karma",
                    "date": "2026-01-02",
                },
            ],
            "tags": ["tag1", "tag2", "tag3"],
        }
        self.mock_db.load.return_value = self.mock_data

        self.mock_material = Mock()
        self.mock_material.mat_id = "mat1"
        self.mock_material.name = "Material 1"
        self.mock_material.fav = False
        self.mock_material.categories = ["cat1"]
        self.mock_material.tags = ["tag1"]
        self.mock_material.renderer = "mantra"
        self.mock_material.date = "2026-01-01"

    @patch("matlib.core.material.Material")
    @patch("matlib.core.database.DatabaseConnector")
    @patch("matlib.prefs.prefs.Prefs")
    @patch("PySide6.QtCore.QAbstractListModel")
    def test_rowCount(
        self, mock_qmodel_init, mock_prefs_class, mock_db_class, mock_material_class
    ):

        mock_qmodel_init.return_value = None
        mock_prefs_class.return_value = self.mock_prefs
        mock_db_class.return_value = self.mock_db
        mock_material_class.return_value = self.mock_material

        mock_mat1 = Mock()
        mock_mat2 = Mock()
        mock_material_class.from_dict.side_effect = [mock_mat1, mock_mat2]

        with patch.object(
            library.MaterialLibrary, "rebuild_thumbs", return_value=None, create=True
        ):

            lib = library.MaterialLibrary()
            count = lib.rowCount()
            self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
