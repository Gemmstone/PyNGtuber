from PyQt6 import QtWidgets, uic, QtCore
from Core.imageGallery import ImageGallery
from Core.Viewer import LayeredImageViewer
from PIL import Image
import pyaudio
import sys


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)

        self.list_microphones()

        self.ImageGallery = ImageGallery()
        self.ImageGallery.selectionChanged.connect(self.getFiles)
        self.scrollArea.setWidget(self.ImageGallery)

        image_list = [
            {
                "route": "Assets/ears/20230411_202335.gif",
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

        self.comboBox.currentIndexChanged.connect(self.setBGColor)

        self.viewer = LayeredImageViewer()
        self.viewerFrame.layout().addWidget(self.viewer)

    def getFiles(self, files):
        print(files)

        images_list = []
        count = 1
        for file in files:
            image = Image.open(file)
            width, height = image.size

            images_list.append({
                "route": file,
                "sizeX": width,
                "sizeY": height,
                "posX": 0,
                "posY": 0,
                "posZ": count,
                "animation": []
            })
            count += 1

        self.viewer.updateImages(images_list)

    def list_microphones(self):
        excluded = ["sysdefault", "surround21", "lavrate", "samplerate", "speexrate", "speex", "upmix", "vdownmix"]

        audio = pyaudio.PyAudio()
        info = audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')

        for i in range(num_devices):
            name = audio.get_device_info_by_host_api_device_index(0, i).get('name')
            if name not in excluded:
                self.microphones.addItem(name)
                if name == "default":
                    self.microphones.setCurrentText(name)

        audio.terminate()

    def event(self, event):
        try:
            if event.type() == QtCore.QEvent.Type.HoverEnter:
                self.showUI()
            elif event.type() == QtCore.QEvent.Type.HoverLeave:
                self.hideUI()
        except AttributeError:
            pass
        return super().event(event)

    def showUI(self):
        self.frame_4.show()
        self.frame.show()
        self.frame_2.show()
        self.frame_3.show()

    def hideUI(self):
        if self.actionHide_UI.isChecked():
            self.frame_4.hide()
            self.frame.hide()
            self.frame_2.hide()
            self.frame_3.hide()
    def setBGColor(self):
        match self.sender().currentText():
            case "Green":
                color = "limegreen"
            case "Magenta":
                color = "magenta"
            case "Cyan":
                color = "cyan"
            case "Blue":
                color = "blue"
            case "Pink":
                color = "hotpink"
            case "Yellow":
                color = "yellow"
            case "White":
                color = "white"
            case _:
                color = "#b8cdee"
        self.viewer.setColor(color)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
