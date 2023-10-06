from PyQt6 import QtWidgets, uic
from Core.imageGallery import ImageGallery
from Core.Viewer import LayeredImageViewer
import sys


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)

        self.ImageGallery = ImageGallery()
        self.scrollArea.setWidget(self.ImageGallery)

        image_list = [
            {
                "route": "Assets/hairback/hairback_039.png",
                "sizeX": 600,
                "sizeY": 600,
                "posX": 0,
                "posY": 0,
                "posZ": 1,
                "animation": []
            },
            {
                "route": "Assets/body/body_017.png",
                "sizeX": 600,
                "sizeY": 600,
                "posX": 0,
                "posY": 0,
                "posZ": 2,
                "animation": []
            }
            # Add more image layers as needed
        ]

        self.viewer = LayeredImageViewer(image_list=image_list)
        self.viewerFrame.layout().addWidget(self.viewer)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
