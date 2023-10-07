from PyQt6 import QtWidgets, uic, QtCore
from Core.imageGallery import ImageGallery
from Core.Viewer import LayeredImageViewer
from PIL import Image
import pyaudio
import json
import sys


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)

        self.list_microphones()

        self.file_parameters = {}
        self.json_file = "parameters.json"

        try:
            with open(self.json_file, "r") as f:
                self.file_parameters = json.load(f)
        except FileNotFoundError:
            pass

        self.ImageGallery = ImageGallery()
        self.ImageGallery.selectionChanged.connect(self.getFiles)
        self.scrollArea.setWidget(self.ImageGallery)

        self.comboBox.currentIndexChanged.connect(self.setBGColor)

        self.viewer = LayeredImageViewer()
        self.viewerFrame.layout().addWidget(self.viewer)

    def save_parameters_to_json(self):
        # Save the file parameters to the JSON file
        with open(self.json_file, "w") as f:
            json.dump(self.file_parameters, f, indent=4)

    def save_current_to_json(self):
        # Save the file parameters to the JSON file
        with open(self.json_file, "w") as f:
            json.dump(self.file_parameters, f, indent=4)

    def getFiles(self, files):
        images_list = []
        count = 1
        for file in files:
            if file in self.file_parameters:
                parameters = self.file_parameters[file]
            else:
                image = Image.open(file)
                width, height = image.size

                parameters = {
                    "sizeX": width,  # Default value for sizeX
                    "sizeY": height,  # Default value for sizeY
                    "posX": 0,  # Default value for posX
                    "posY": 0,  # Default value for posY
                    "posZ": count,  # Default value for posZ
                    "animation": []  # Default value for animation
                }

                self.file_parameters[file] = parameters  # Store default parameters

            images_list.append({
                "route": file,
                **parameters  # Include the parameters in the dictionary
            })
            count += 1

        self.viewer.updateImages(images_list)

        # self.save_parameters_to_json()

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
