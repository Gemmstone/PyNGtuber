from PyQt5 import QtWidgets, uic
from Core.imageGallery import ImageGallery
from Core.Viewer import LayeredImageViewer


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)

        self.ImageGallery = ImageGallery()
        self.scrollArea.setWidget(self.ImageGallery)

        self.viewer = LayeredImageViewer()
        self.viewerFrame.layout().addWidget(self.viewer)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
