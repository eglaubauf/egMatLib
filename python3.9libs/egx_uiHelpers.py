from PySide2 import QtCore
from PySide2 import QtWidgets


class ClickSlider(QtWidgets.QSlider):
    def __init__(self):
        super(ClickSlider, self).__init__()

    def mouseClickEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            e.accept()
            x = e.pos().x()
            value = (
                self.maximum() - self.minimum()
            ) * x / self.width() + self.minimum()

            try:
                stepSize = abs(self.value - value)
                self.setPageStep(stepSize)
                self.setSingleStep(stepSize)
            except:
                pass
        else:
            return super().mouseClickEvent(e)

    def mouseMoveEvent(self, e):
        e.accept()
        x = e.pos().x()
        value = (self.maximum() - self.minimum()) * x / self.width() + self.minimum()

        try:
            stepSize = abs(self.value - value)

            self.setPageStep(stepSize)
            self.setSingleStep(stepSize)
        except:
            pass
        self.setValue(value)
