"""
Unit tests for library.py

This module contains comprehensive unit tests for the MaterialLibrary and ThumbnailWorker classes.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from PySide6 import QtCore
import hou


class TestMaterialLibrary(unittest.TestCase):
    """Test suite for MaterialLibrary class"""

    def setUp(self):
        """Set up test fixtures and mocks"""
        # Patch all external dependencies
        self.prefs_patcher = patch("matlib.core.library.prefs.Prefs")
        self.db_patcher = patch("matlib.core.library.database.DatabaseConnector")
        self.material_patcher = patch("matlib.core.library.material.Material")
        self.thumbs_patcher = patch("matlib.core.library.thumbs.ThumbNailRenderer")
        self.nodes_patcher = patch("matlib.core.library.nodes.NodeHandler")
        self.qimage_patcher = patch("PySide6.QtGui.QImage")

        self.mock_prefs_cls = self.prefs_patcher.start()
        self.mock_db_cls = self.db_patcher.start()
        self.mock_material_cls = self.material_patcher.start()
        self.mock_thumbs_cls = self.thumbs_patcher.start()
        self.mock_nodes_cls = self.nodes_patcher.start()
        self.mock_hou = Mock()
        self.mock_qimage_cls = self.qimage_patcher.start()

        # Configure preferences mock
        self.mock_prefs = Mock()
        self.mock_prefs.dir = "/test/dir"
        self.mock_prefs.img_dir = "/img/"
        self.mock_prefs.asset_dir = "/assets/"
        self.mock_prefs.ext = ".mat"
        self.mock_prefs.img_ext = ".png"
        self.mock_prefs.thumbsize = 256
        self.mock_prefs.render_on_import = False
        self.mock_prefs_cls.return_value = self.mock_prefs

        # Configure database mock
        self.mock_db = Mock()
        self.asset_data = {
            "name": "TestMaterial",
            "categories": ["metal", "rough"],
            "tags": ["test", "sample"],
            "fav": False,
            "renderer": "karma",
            "date": "2026-02-08",
            "mat_id": "mat_001",
        }
        self.mock_db.load.return_value = {
            "tags": ["test", "sample"],
            "assets": [self.asset_data],
        }
        self.mock_db_cls.return_value = self.mock_db

        # Configure material mock
        self.mock_material = Mock()
        self.mock_material.name = "TestMaterial"
        self.mock_material.categories = ["metal", "rough"]
        self.mock_material.tags = ["test", "sample"]
        self.mock_material.fav = False
        self.mock_material.renderer = "karma"
        self.mock_material.date = "2026-02-08"
        self.mock_material.mat_id = "mat_001"
        self.mock_material.get_as_dict.return_value = self.asset_data
        self.mock_material_cls.from_dict.return_value = self.mock_material

        # Mock QImage
        self.mock_qimage = Mock()
        self.mock_qimage.scaled.return_value = self.mock_qimage
        self.mock_qimage_cls.return_value = self.mock_qimage

        # Mock hou environment
        self.mock_hou.getenv.return_value = "/fake/path"

        # Patch worker creation to avoid threading
        self.worker_patcher = patch("matlib.core.library.MaterialLibrary._start_worker")
        self.mock_start_worker = self.worker_patcher.start()

        # Import and create library instance
        from matlib.core import library

        self.library = library.MaterialLibrary()

    def tearDown(self):
        """Clean up patches"""
        patch.stopall()

    def test_initialization(self):
        """Test MaterialLibrary initializes correctly"""
        self.assertIsNotNone(self.library.preferences)
        self.assertEqual(len(self.library._assets), 1)
        self.assertEqual(self.library._tags, ["test", "sample"])
        self.assertEqual(self.library._thumbsize, 256)

    def test_row_count(self):
        """Test rowCount returns correct number of assets"""
        self.assertEqual(self.library.rowCount(), 1)

    def test_data_display_role(self):
        """Test data() returns correct display name"""
        index = self.library.index(0, 0)
        result = self.library.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
        self.assertEqual(result, "TestMaterial")

    def test_data_decoration_role(self):
        """Test data() returns thumbnail for decoration role"""
        index = self.library.index(0, 0)
        result = self.library.data(index, QtCore.Qt.ItemDataRole.DecorationRole)
        # Should return default image since thumb not loaded
        self.assertIsNotNone(result)

    def test_data_category_role(self):
        """Test data() returns categories"""
        index = self.library.index(0, 0)
        result = self.library.data(index, self.library.CategoryRole)
        self.assertEqual(result, ["metal", "rough"])

    def test_data_tag_role(self):
        """Test data() returns tags"""
        index = self.library.index(0, 0)
        result = self.library.data(index, self.library.TagRole)
        self.assertEqual(result, ["test", "sample"])

    def test_data_favorite_role(self):
        """Test data() returns favorite status"""
        index = self.library.index(0, 0)
        result = self.library.data(index, self.library.FavoriteRole)
        self.assertEqual(result, False)

    def test_data_renderer_role(self):
        """Test data() returns renderer"""
        index = self.library.index(0, 0)
        result = self.library.data(index, self.library.RendererRole)
        self.assertEqual(result, "karma")

    def test_data_date_role(self):
        """Test data() returns date"""
        index = self.library.index(0, 0)
        result = self.library.data(index, self.library.DateRole)
        self.assertEqual(result, "2026-02-08")

    def test_data_id_role(self):
        """Test data() returns material ID"""
        index = self.library.index(0, 0)
        result = self.library.data(index, self.library.IdRole)
        self.assertEqual(result, "mat_001")

    def test_sanitize_tags(self):
        """Test tag sanitization removes spaces and duplicates"""
        result = self.library.sanitize_tags("tag1, tag2 , tag1, tag3")
        tags = set(result.split(","))
        self.assertEqual(tags, {"tag1", "tag2", "tag3"})

    def test_sanitize_tags_empty(self):
        """Test sanitize_tags handles empty string"""
        result = self.library.sanitize_tags("")
        self.assertEqual(result, "")

    def test_check_add_tags_new_tag(self):
        """Test check_add_tags adds new tags"""
        self.library._tags = ["existing"]
        self.library.check_add_tags("existing,newtag")
        self.assertIn("newtag", self.library._tags)

    def test_check_add_tags_existing_tag(self):
        """Test check_add_tags doesn't duplicate existing tags"""
        self.library._tags = ["existing"]
        initial_count = len(self.library._tags)
        self.library.check_add_tags("existing")
        self.assertEqual(len(self.library._tags), initial_count)

    def test_assets_property(self):
        """Test assets property returns asset list"""
        assets = self.library.assets
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0].name, "TestMaterial")

    def test_tags_property(self):
        """Test tags property returns tag list"""
        tags = self.library.tags
        self.assertEqual(tags, ["test", "sample"])

    def test_thumbsize_property_getter(self):
        """Test thumbsize property getter"""
        self.assertEqual(self.library.thumbsize, 256)

    def test_thumbsize_property_setter(self):
        """Test thumbsize property setter"""
        self.library.thumbsize = 512
        self.assertEqual(self.library.thumbsize, 512)

    def test_save(self):
        """Test save() writes data to database"""
        self.library.save()
        self.mock_db.set.assert_called_once()
        self.mock_db.save.assert_called_once()

    def test_toggle_fav_false_to_true(self):
        """Test toggling favorite from False to True"""
        self.library._assets[0].fav = False
        index = self.library.index(0, 0)

        self.library.toggle_fav(index)

        self.assertTrue(self.library._assets[0].fav)
        # self.assertIn(index, self.library._outofdate_thumb_list)

    def test_toggle_fav_true_to_false(self):
        """Test toggling favorite from True to False"""
        self.library._assets[0].fav = True
        index = self.library.index(0, 0)

        self.library.toggle_fav(index)

        self.assertFalse(self.library._assets[0].fav)

    def test_set_assetdata_normal_values(self):
        """Test set_assetdata with normal values"""
        index = self.library.index(0, 0)

        self.library.set_assetdata(index, "NewName", "cat1,cat2", "tag1,tag2", True)

        self.mock_material.set_data.assert_called()

    def test_set_assetdata_multiple_values_placeholder(self):
        """Test set_assetdata preserves existing data when Multiple Values placeholder used"""
        index = self.library.index(0, 0)
        original_name = self.library._assets[0].name

        self.library.set_assetdata(index, "Multiple Values...", "cat1", "tag1", False)

        # Name should be preserved (not changed to placeholder)
        call_args = self.mock_material.set_data.call_args
        # First arg should still be original name
        self.assertNotEqual(call_args[0][0], "Multiple Values...")

    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_remove_asset(self, mock_remove, mock_exists):
        """Test remove_asset deletes files and removes from library"""
        index = self.library.index(0, 0)
        initial_count = self.library.rowCount()

        self.library.remove_asset(index)

        # Should remove 3 files (.mat, .png, .interface)
        self.assertEqual(mock_remove.call_count, 3)
        self.assertEqual(self.library.rowCount(), initial_count - 1)

    def test_remove_asset_invalid_index(self):
        """Test remove_asset with invalid index does nothing"""
        invalid_index = self.library.index(99, 0)
        initial_count = self.library.rowCount()

        self.library.remove_asset(invalid_index)

        self.assertEqual(self.library.rowCount(), initial_count)

    def test_rename_category(self):
        """Test rename_category updates all assets"""
        self.library.rename_category("metal", "metallic")

        self.mock_material.rename_category.assert_called_once_with("metal", "metallic")

    def test_remove_category(self):
        """Test remove_category removes from all assets"""
        self.library.remove_category("metal")

        self.mock_material.remove_category.assert_called_once_with("metal")

    def test_add_asset(self):
        """Test add_asset creates new material"""
        mock_node = Mock()
        mock_node.name.return_value = "NewMaterial"

        mock_handler = Mock()
        mock_handler.get_renderer_from_node.return_value = "karma"
        mock_handler.save_node.return_value = True
        self.mock_nodes_cls.return_value = mock_handler

        new_mat = Mock()
        new_mat.mat_id = "mat_002"
        self.mock_material_cls.return_value = new_mat

        renderer = self.library.add_asset(mock_node, "metal", "test", False)

        self.assertEqual(renderer, "karma")
        mock_handler.save_node.assert_called_once()

    def test_add_asset_from_strings(self):
        """Test add_asset_from_strings creates asset from strings"""
        new_mat = Mock()
        new_mat.mat_id = "mat_003"
        self.mock_material_cls.return_value = new_mat

        result = self.library.add_asset_from_strings(
            "Material", "cat1", "tag1", True, "karma"
        )

        new_mat.set_data.assert_called_once()
        self.assertIs(result, self.library._assets[-1])

    def test_flags(self):
        """Test flags returns correct item flags"""
        index = self.library.index(0, 0)
        flags = self.library.flags(index)

        # Should include drag enabled
        self.assertTrue(flags & QtCore.Qt.ItemFlag.ItemIsDragEnabled)

    def test_set_custom_iconsize(self):
        """Test set_custom_iconsize updates thumbnail size"""
        new_size = QtCore.QSize(512, 512)

        self.library.set_custom_iconsize(new_size)

        self.assertEqual(self.library._thumbsize, 512)

    @patch("hou.ui.paneTabs")
    def test_get_current_network_node(self, mock_pane_tabs):
        """Test get_current_network_node returns current node"""
        mock_tab = Mock()
        mock_tab.type.return_value = hou.paneTabType.NetworkEditor
        mock_node = Mock()
        mock_tab.currentNode.return_value = mock_node

        mock_pane_tabs.return_value = [mock_tab]

        result = self.library.get_current_network_node()

        self.assertIs(result, mock_node)

    @patch("hou.ui.paneTabs")
    def test_get_current_network_node_none_found(self, mock_pane_tabs):
        """Test get_current_network_node returns None when no network editor"""
        mock_tab = Mock()
        mock_tab.type.return_value = Mock()  # Not NetworkEditor type

        mock_pane_tabs = MagicMock()
        mock_pane_tabs.return_value = [mock_tab]

        result = self.library.get_current_network_node()

        self.assertIsNone(result)

    def test_render_thumbnail(self):
        """Test render_thumbnail creates thumbnail for asset"""
        mock_renderer = Mock()
        self.mock_thumbs_cls.return_value = mock_renderer

        index = self.library.index(0, 0)
        self.library.render_thumbnail(index)

        mock_renderer.create_thumbnail.assert_called_once()
        self.assertTrue(self.library._force_render == False)  # Reset after render

    def test_import_asset_to_scene(self):
        """Test import_asset_to_scene imports asset to Houdini"""
        mock_importer = Mock()
        self.mock_nodes_cls.return_value = mock_importer

        index = self.library.index(0, 0)
        self.library.import_asset_to_scene(index)

        mock_importer.import_asset_to_scene.assert_called_once_with(self.mock_material)

    @patch("os.listdir")
    @patch("os.path.exists")
    @patch("os.remove")
    def test_cleanup_db_removes_orphan_files(
        self, mock_remove, mock_exists, mock_listdir
    ):
        """Test cleanup_db removes orphaned files from disk"""
        # Setup: asset files exist, but extra orphan file
        mock_exists.return_value = True
        mock_listdir.side_effect = [
            ["mat_001.mat", "orphan.mat"],  # assets dir
            ["mat_001.png", "orphan.png"],  # img dir
        ]

        hou.ui = MagicMock()
        hou.ui.displayMessage.return_value = None
        self.library.cleanup_db()

        # Should remove orphan files
        self.assertTrue(mock_remove.called)


if __name__ == "__main__":
    unittest.main()
