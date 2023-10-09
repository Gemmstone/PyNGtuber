from PyQt6 import QtWidgets, uic, QtCore
from Core.imageGallery import ImageGallery
from Core.Viewer import LayeredImageViewer
from Core.Settings import SettingsToolBox
from PIL import Image
import pyaudio
import json
import copy
import sys


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("UI/main.ui", self)

        self.list_microphones()

        self.color = (184, 205, 238)  # Default to a light blue color
        self.file_parameters = {}
        self.current_files = []
        self.json_file = "Data/parameters.json"
        self.current_json_file = "Data/current.json"

        try:
            with open(self.json_file, "r") as f:
                self.file_parameters = json.load(f)
        except FileNotFoundError:
            pass

        try:
            with open(self.current_json_file, "r") as f:
                self.current_files = json.load(f)
        except FileNotFoundError:
            pass

        self.ImageGallery = ImageGallery(self.current_files)
        self.ImageGallery.selectionChanged.connect(self.getFiles)
        self.scrollArea.setWidget(self.ImageGallery)

        self.SettingsGallery = SettingsToolBox()
        self.SettingsGallery.settings_changed.connect(self.saveSettings)
        self.scrollArea_2.setWidget(self.SettingsGallery)

        self.comboBox.currentIndexChanged.connect(self.setBGColor)

        self.viewer = LayeredImageViewer()
        self.viewerFrame.layout().addWidget(self.viewer)
        self.viewer.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.getFiles(self.current_files, opening=True)

        self.actionSave_Current_Avatar_As.triggered.connect(self.save_screenshot)

    def save_screenshot(self):
        screenshot = self.viewer.grab()
        qimage = screenshot.toImage()
        image = Image.fromqpixmap(qimage)
        image = image.convert("RGBA")

        image_data = list(image.getdata())

        new_image_data = []

        color_map = {
            "Green": (50, 205, 50),  # Lime Green
            "Magenta": (255, 0, 255),  # Magenta
            "Cyan": (0, 255, 255),  # Cyan
            "Blue": (0, 0, 255),  # Blue
            "Pink": (255, 105, 180),  # Hot Pink
            "Yellow": (255, 255, 0),  # Yellow
            "White": (255, 255, 255),  # White
        }

        target_color = color_map.get(self.comboBox.currentText())
        if target_color is None:
            target_color = (184, 205, 238)

        tolerance = 30
        for pixel in image_data:
            r, g, b, a = pixel
            if abs(r - target_color[0]) <= tolerance and \
                    abs(g - target_color[1]) <= tolerance and \
                    abs(b - target_color[2]) <= tolerance:
                new_image_data.append((r, g, b, 0))
            else:
                new_image_data.append((r, g, b, a))

        image.putdata(new_image_data)
        image.save("output.png")

    def saveSettings(self, settings):
        self.file_parameters[settings['route']] = copy.deepcopy(settings)
        self.file_parameters[settings['route']].pop("route")
        self.getFiles(self.current_files)

    def save_parameters_to_json(self):
        # Save the file parameters to the JSON file
        with open(self.json_file, "w") as f:
            json.dump(self.file_parameters, f, indent=4)

        with open(self.current_json_file, "w") as f:
            json.dump(self.current_files, f, indent=4)

    def getFiles(self, files=None, opening=False):
        images_list = []
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
                    "posZ": 40,  # Default value for posZ
                    "blinking": "ignore",
                    "talking": "ignore",
                    "css": "",
                    "hotkeys": [],
                    "animation": []  # Default value for animation
                }

                self.file_parameters[file] = parameters  # Store default parameters

            images_list.append({
                "route": file,
                **parameters  # Include the parameters in the dictionary
            })

        self.viewer.updateImages(images_list, self.color)

        if self.current_files != files or opening:
            self.SettingsGallery.set_items(images_list)
        self.current_files = files

        self.save_parameters_to_json()
        QtCore.QTimer.singleShot(300, self.setBGColor)

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
        self.frame_5.show()
        self.frame_3.show()
        self.frame_8.show()
        self.viewerFrame_2.setStyleSheet(f"border-radius: 20px; background-color: {self.color}")

    def hideUI(self):
        if self.HideUI.isChecked():
            self.frame_4.hide()
            self.frame_5.hide()
            self.frame_3.hide()
            self.frame_8.hide()
            self.viewerFrame_2.setStyleSheet(f"background-color: {self.color}")

    def setBGColor(self):
        match self.comboBox.currentText():
            case "Green":
                self.color = "limegreen"
            case "Magenta":
                self.color = "magenta"
            case "Cyan":
                self.color = "cyan"
            case "Blue":
                self.color = "blue"
            case "Pink":
                self.color = "hotpink"
            case "Yellow":
                self.color = "yellow"
            case "White":
                self.color = "white"
            case _:
                self.color = "#b8cdee"

        self.viewer.setColor(self.color)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    screen = app.primaryScreen()
    screen_geometry = screen.availableGeometry()
    quarter_width = int(screen_geometry.width() // 1.7)
    quarter_height = int(screen_geometry.height() // 1.5)
    window = MainWindow()
    window.setGeometry(100, 100, quarter_width, quarter_height)
    window.show()
    app.exec()
