from PySide6 import QtWidgets, QtCore, QtGui


class ClickSlider(QtWidgets.QSlider):
    def __init__(self) -> None:
        super(ClickSlider, self).__init__()

    def mouseClickEvent(self, e: QtGui.QMouseEvent):
        if e.button() == QtCore.Qt.LeftButton:
            e.accept()
            x = e.pos().x()
            value = (
                self.maximum() - self.minimum()
            ) * x / self.width() + self.minimum()

            try:

                stepsize = int(abs(self.value() - value))
                self.setPageStep(stepsize)
                self.setSingleStep(stepsize)
            except Exception:
                pass
        else:
            return super().mouseClickEvent(e)

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        ev.accept()
        x = ev.pos().x()
        value = (self.maximum() - self.minimum()) * x / self.width() + self.minimum()

        try:
            stepsize = int(abs(self.value() - value))
            self.setPageStep(stepsize)
            self.setSingleStep(stepsize)
        except Exception:
            pass
        self.setValue(int(value))
