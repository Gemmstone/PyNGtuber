from Core.ShortcutsManager import MidiListener, KeyboardListener
from Core.imageGallery import ImageGallery, ExpressionSelector
from Core.audioManager import MicrophoneVolumeWidget
from PIL import Image, ImageSequence, ImageOps
from Core.Viewer import LayeredImageViewer
from Core.Settings import SettingsToolBox
from PyQt6 import QtWidgets, uic, QtCore
from PyQt6.QtCore import QTimer
from collections import Counter
from pathlib import Path
import json
import copy
import sys


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("UI/main.ui", self)

        self.color = (184, 205, 238)  # Default to a light blue color
        self.file_parameters = {}
        self.current_files = []
        self.json_file = "Data/parameters.json"
        self.current_json_file = "Data/current.json"

        self.midi_listener = MidiListener()
        self.keyboard_listener = KeyboardListener()

        self.midi_listener.update_shortcuts_signal.connect(self.shortcut_received)
        self.keyboard_listener.update_shortcuts_signal.connect(self.shortcut_received)

        self.midi_listener.start()
        self.keyboard_listener.start()

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

        self.audio = MicrophoneVolumeWidget()
        self.audio.activeAudio.connect(self.audioStatus)
        self.audioFrame.layout().addWidget(self.audio)

        self.ImageGallery = ImageGallery(self.current_files)
        self.ImageGallery.selectionChanged.connect(self.update_viewer)
        self.scrollArea.setWidget(self.ImageGallery)

        self.SettingsGallery = SettingsToolBox()
        self.SettingsGallery.settings_changed.connect(self.saveSettings)
        self.scrollArea_2.setWidget(self.SettingsGallery)

        self.comboBox.currentIndexChanged.connect(self.setBGColor)

        self.viewer = LayeredImageViewer()
        self.viewerFrame.layout().addWidget(self.viewer)
        self.viewer.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.expressionSelector = ExpressionSelector("Assets")
        self.scrollArea_5.setWidget(self.expressionSelector)

        self.setBGColor()
        self.showUI()
        self.update_viewer(self.current_files, opening=True)

        self.PNG1.clicked.connect(lambda: self.export_png(1))
        self.PNG2.clicked.connect(lambda: self.export_png(2))

        self.save.clicked.connect(self.save_avatar)

    def save_avatar(self):
        print(self.current_files)
        print(self.file_parameters)

    def export_png(self, method):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption=self.tr("Save File"),
            directory=str(Path.home()),
            filter=self.tr("Images (*.png)"))

        if fileName:
            if not fileName.lower().endswith(".png"):
                fileName += ".png"
            self.image_generator(output_name=fileName, method=method)

    def shortcut_received(self, shortcuts):
        print(f"Received: {shortcuts}")

    def audioStatus(self, status):
        if status == -1:
            self.audio.active_audio_signal = -1
            status = 0
        self.viewer.page().runJavaScript(
            '''
            var elementsOpen = document.getElementsByClassName("talking_open");
            var elementsClosed = document.getElementsByClassName("talking_closed");
            var elementsScreaming = document.getElementsByClassName("talking_screaming");
            var imageWrapper = document.getElementById("image-wrapper");

            var opacityOpen = ''' + str(1 if status == 1 else 0) + ''';
            var opacityClosed = ''' + str(1 if status == 0 else 0) + ''';
            var opacityScreaming = ''' + str(1 if status == 2 else 0) + ''';

            // Apply CSS transitions for a smooth animation to text elements
            for (var i = 0; i < elementsOpen.length; i++) {
                elementsOpen[i].style.transition = "opacity 0.3s"; // Adjust the duration as needed
                elementsOpen[i].style.opacity = opacityOpen;
            }

            for (var i = 0; i < elementsClosed.length; i++) {
                elementsClosed[i].style.transition = "opacity 0.3s"; // Adjust the duration as needed
                elementsClosed[i].style.opacity = opacityClosed;
            }

            for (var i = 0; i < elementsScreaming.length; i++) {
                elementsScreaming[i].style.transition = "opacity 0.3s"; // Adjust the duration as needed
                elementsScreaming[i].style.opacity = opacityScreaming;
            }

            // Add a CSS animation for jumping the image-wrapper
            if (''' + str(status) + ''' == 1 || ''' + str(status) + ''' == 2) {
                imageWrapper.style.animation = "floaty 0.5s ease-in-out infinite"; 
            } else {
                imageWrapper.style.animation = "floaty 6s ease-in-out infinite";
            }
            '''
        )

    def saveSettings(self, settings):
        self.file_parameters[settings['route']] = copy.deepcopy(settings)
        self.file_parameters[settings['route']].pop("route")
        self.update_viewer(self.current_files)

    def save_parameters_to_json(self, save_default):
        # Save the file parameters to the JSON file
        if save_default:
            pass
        else:
            with open(self.json_file, "w") as f:
                json.dump(self.file_parameters, f, indent=4)

        with open(self.current_json_file, "w") as f:
            json.dump(self.current_files, f, indent=4)

    def image_generator(self, output_name, method=1):
        files = [
            i for i in self.getFiles(self.current_files)
            if i["blinking"] in ["ignore", "blinking_open"] and
               i["talking"] in ["ignore", "talking_closed"]
        ]
        images = []

        if method == 1:
            size_counter = Counter()

            for file_data in files:
                file_route = file_data["route"]
                rotation = file_data["rotation"]
                posZ = file_data["posZ"]
                posX = file_data["posX"]
                posY = file_data["posY"]
                sizeX = file_data["sizeX"]
                sizeY = file_data["sizeY"]

                if file_route.lower().endswith((".png", ".jpg", ".jpeg")):
                    image = Image.open(file_route)
                elif file_route.lower().endswith((".gif", ".webp")):
                    image = Image.open(file_route)

                    # Handle GIF and WebP animations by extracting the middle frame
                    if isinstance(image, Image.Image):
                        frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
                        num_frames = len(frames)
                        middle_frame_index = num_frames // 2
                        image = frames[middle_frame_index]

                # Apply rotation
                if rotation != 0:
                    image = image.rotate(rotation * -1, expand=True)

                # Resize the image if necessary
                if sizeX != image.width or sizeY != image.height:
                    image = image.resize((sizeX, sizeY))

                # Count the size occurrence
                size_counter[(sizeX, sizeY)] += 1

                # Calculate adjusted position
                images.append((image, posZ, posX, posY))

                # Find the most used size
            most_used_size = size_counter.most_common(1)[0][0]

            if images:
                images.sort(key=lambda x: x[1])  # Sort by posZ

                # Create a blank canvas with a transparent background
                canvas = Image.new("RGBA", (most_used_size[0], most_used_size[1]), (0, 0, 0, 0))

                for image, _, posX, posY in images:
                    # Use alpha compositing to blend images with transparency
                    canvas = Image.alpha_composite(
                        canvas, ImageOps.fit(
                            image, (most_used_size[0], most_used_size[1]), method=0, bleed=0.0, centering=(0.5, 0.5)
                        )
                    )

                canvas.save(output_name, "PNG")

        elif method == 2:
            for file_data in files:
                file_route = file_data["route"]
                rotation = file_data["rotation"]
                posZ = file_data["posZ"]
                posX = file_data["posX"]
                posY = file_data["posY"]
                sizeX = file_data["sizeX"]
                sizeY = file_data["sizeY"]

                if file_route.lower().endswith((".png", ".jpg", ".jpeg")):
                    image = Image.open(file_route)
                elif file_route.lower().endswith((".gif", ".webp")):
                    image = Image.open(file_route)

                    # Handle GIF and WebP animations by extracting the middle frame
                    if isinstance(image, Image.Image):
                        frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
                        num_frames = len(frames)
                        middle_frame_index = num_frames // 2
                        image = frames[middle_frame_index]

                # Apply rotation
                if rotation != 0:
                    image = image.rotate(rotation * -1, expand=True)

                # Resize the image if necessary
                if sizeX != image.width or sizeY != image.height:
                    image = image.resize((sizeX, sizeY))

                # Calculate the center of the Qt window
                center_x = self.width() // 2
                center_y = self.height() // 2

                # Adjust the position to account for the center
                adjusted_posX = center_x + posX - (image.width / 2)
                adjusted_posY = center_y + posY - (image.height / 2)

                images.append((image, posZ, adjusted_posX, adjusted_posY))

            if images:
                images.sort(key=lambda x: x[1])  # Sort by posZ

                # Calculate the size of the canvas based on the Qt window size
                max_width, max_height = self.width(), self.height()

                # Create a blank canvas to paste images on
                canvas = Image.new("RGBA", (max_width, max_height))

                for image, _, posX, posY in images:
                    canvas.paste(image, (int(posX), int(posY)), image)

                canvas.save(output_name, "PNG")

    def getFiles(self, files):
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
                    "use_css": False,
                    "hotkeys": [],
                    "animation": [],  # Default value for animation
                    "rotation": 0,
                }

                self.file_parameters[file] = parameters  # Store default parameters

            images_list.append({
                "route": file,
                **parameters  # Include the parameters in the dictionary
            })
        return images_list

    def update_viewer(self, files=None, opening=False, save_default=True):
        images_list = self.getFiles(files)

        self.viewer.updateImages(images_list, self.color)
        if self.current_files != files or opening:
            self.SettingsGallery.set_items(images_list)
        self.current_files = files
        self.save_parameters_to_json(save_default=save_default)
        QTimer.singleShot(500, lambda: self.audioStatus(-1))


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
        match self.comboBox.currentIndex():
            case 0:
                self.color = "limegreen"
            case 1:
                self.color = "magenta"
            case 2:
                self.color = "cyan"
            case 3:
                self.color = "blue"
            case 4:
                self.color = "hotpink"
            case 5:
                self.color = "yellow"
            case 6:
                self.color = "white"
            case _:
                self.color = "#b8cdee"

        self.viewer.setColor(self.color)

    def stop_all_workers(self):
        # Call the stop_thread method for each worker
        self.audio.audio_thread.stop_stream()
        self.midi_listener.quit()
        self.midi_listener.wait()
        self.keyboard_listener.quit()
        self.keyboard_listener.wait()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.aboutToQuit.connect(window.stop_all_workers)
    app.exec()
