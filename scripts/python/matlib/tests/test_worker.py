import unittest
from unittest.mock import Mock, MagicMock, patch, call
import sys
from typing import Any


# Mock the dependencies before importing library
# sys.modules["PySide6"] = Mock()
# sys.modules["PySide6.QtCore"] = Mock()
# sys.modules["PySide6.QtGui"] = Mock()
# sys.modules["hou"] = MagicMock()
# sys.modules["matlib"] = MagicMock()
# sys.modules["matlib.core"] = MagicMock()
# sys.modules["matlib.core.material"] = MagicMock()
# sys.modules["matlib.core.database"] = MagicMock()
# sys.modules["matlib.prefs"] = MagicMock()
# sys.modules["matlib.prefs.prefs"] = MagicMock()
# sys.modules["matlib.render"] = MagicMock()
# sys.modules["matlib.render.thumbs"] = MagicMock()
# sys.modules["matlib.render.nodes"] = MagicMock()

# Import after mocking
# from PySide6 import QtCore, QtGui
from matlib.core import library


class TestThumbnailWorker(unittest.TestCase):
    """Test suite for ThumbnailWorker class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_parent = Mock()
        self.items = [
            ("/path/to/image1.png", False, 0),
            ("/path/to/image2.png", True, 1),
            ("/path/to/image3.png", False, 2),
        ]
        self.size = 512

    @patch("PySide6.QtGui.QImage")
    @patch("PySide6.QtGui.QPainter")
    @patch("PySide6.QtCore.QThread.__init__")
    def test_init(self, mock_qthread_init, mock_qpainter, mock_qimage):
        """Test ThumbnailWorker initialization"""
        mock_qthread_init.return_value = None

        worker = library.ThumbnailWorker(self.items, self.size, self.mock_parent)

        self.assertEqual(worker._items, self.items)
        self.assertEqual(worker._size, self.size)
        mock_qthread_init.assert_called_once()

    @patch("PySide6.QtGui.QImage")
    @patch("PySide6.QtGui.QPainter")
    @patch("PySide6.QtCore.QThread.__init__")
    def test_run_without_favorites(
        self, mock_qthread_init, mock_qpainter_class, mock_qimage_class
    ):
        """Test run method without favorite images"""
        mock_qthread_init.return_value = None

        mock_image = Mock()
        mock_image.isNull.return_value = False
        mock_image.scaled.return_value = mock_image
        mock_qimage_class.return_value = mock_image

        worker = library.ThumbnailWorker([("/path/test.png", False, 0)], self.size)
        worker.thumbnail_ready = Mock()
        worker.thumbnail_ready.emit = Mock()

        worker.run()

        worker.thumbnail_ready.emit.assert_called()

    @patch("PySide6.QtGui.QImage")
    @patch("PySide6.QtGui.QPainter")
    @patch("PySide6.QtCore.QThread.__init__")
    def test_run_with_favorites(
        self, mock_qthread_init, mock_qpainter_class, mock_qimage_class
    ):
        """
        Mock run method with favorite images
        """

        mock_qthread_init.return_value = None

        mock_image = Mock()
        mock_image.isNull.return_value = False
        mock_image.scaled.return_value = mock_image
        mock_qimage_class.return_value = mock_image

        worker = library.ThumbnailWorker([("/path/test.png", True, 0)], self.size)
        worker.thumbnail_ready = Mock()
        worker.thumbnail_ready.emit = Mock()

        worker.run()

        worker.thumbnail_ready.emit.assert_called()

    @patch("PySide6.QtGui.QImage")
    @patch("PySide6.QtGui.QPainter")
    @patch("PySide6.QtCore.QThread.__init__")
    def test_run_with_null_image(
        self, mock_qthread_init, mock_qpainter, mock_qimage_class
    ):
        """Test run method handles null images correctly"""
        mock_qthread_init.return_value = None

        mock_image = Mock()
        mock_image.isNull.return_value = True
        mock_qimage_class.return_value = mock_image

        worker = library.ThumbnailWorker([("/path/null.png", False, 0)], self.size)
        worker.thumbnail_ready = Mock()
        worker.thumbnail_ready.emit = Mock()

        worker.run()

        worker.thumbnail_ready.emit.assert_not_called()
