from PySide6 import QtWidgets, QtGui
import hou
from datetime import datetime


class DragDropListView(QtWidgets.QListView):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        self.state = False
        self.currtime = 0
        super().__init__(parent)

    def dragLeaveEvent(self, e: QtGui.QDragLeaveEvent) -> None:

        panel = None
        if not self.state:
            if hou.ui.paneTabUnderCursor():
                if hou.ui.paneTabUnderCursor().type().name() != "PythonPanel":
                    self.state = True
                    panel = (
                        self.parentWidget()
                        .parentWidget()
                        .parentWidget()
                        .parentWidget()
                        .parentWidget()
                    )

        # Avoid multiple imports since dragLeave is fired multiple times and houdini as no way to catch a drop from another panel
        if self.state:
            if panel:
                panel.import_asset()
                self.state = False


class DragDropCentralWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = False
        self.index_saved = []
        self.currtime = 0

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        node_path = event.mimeData().text()
        # Check if valid data:
        if not hou.node(node_path):
            return
        hou.node(node_path).setSelected(True)  # Select node for save script
        panel = self.parentWidget().parentWidget()
        panel.save_asset()
        self.state = False

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent) -> None:
        print("Leave")
        if not self.state:
            if hou.ui.paneTabUnderCursor():
                if hou.ui.paneTabUnderCursor().type().name() != "PythonPanel":
                    self.state = True
                    panel = self.parentWidget().parentWidget()
                    # Restore Selection if we need it
                    for index in self.index_saved:
                        panel.thumblist.setCurrentIndex(index)

        # Avoid multiple imports since dragLeave is fired multiple times and houdini as no way to catch a drop from another panel
        if self.state:
            print("Import")
            # Import if we didn't register an import recently
            sec = datetime.time(datetime.now()).second
            msec = datetime.time(datetime.now()).microsecond / 1000000
            time = sec + msec
            diff = abs(time - self.currtime)
            if self.currtime != 0:
                if diff > 0.15:
                    self.currtime = time
                    panel = self.parentWidget().parentWidget()
                    panel.import_asset()
                    self.state = False
                    event.accept()
                else:
                    return  # Wait and avoid multiimport
            else:
                # Import on first Drag
                self.currtime = time
                panel = self.parentWidget().parentWidget()
                panel.import_asset()
                event.accept()
                self.state = False

        return super().dragLeaveEvent(event)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        print("Enter")
        panel = self.parentWidget().parentWidget()
        # Clear and store selection if not empty so we avoid accidental import
        if panel.thumblist.selectedIndexes():
            self.index_saved = panel.thumblist.selectedIndexes()
            panel.thumblist.clearSelection()

        return super().dragEnterEvent(event)
