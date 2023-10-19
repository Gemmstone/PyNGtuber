from Core.imageGallery import ImageGallery, ExpressionSelector, ModelGallery
from Core.ShortcutsManager import MidiListener, KeyboardListener
from Core.audioManager import MicrophoneVolumeWidget
from PyQt6.QtCore import pyqtSlot, QCoreApplication, pyqtSignal
from PIL import Image, ImageSequence, ImageOps
from Core.Viewer import LayeredImageViewer
from Core.Settings import SettingsToolBox
from PyQt6 import QtWidgets, uic, QtCore
from collections import Counter
from PyQt6.QtGui import QIcon
from pathlib import Path
import subprocess
import json
import copy
import mido
import sys
import os


class ShortcutsDialog(QtWidgets.QDialog):
    new_command = pyqtSignal(dict)

    def __init__(self, midi_listener, keyboard_listener, data, parent=None):
        super().__init__(parent)

        self.midi_listener = midi_listener
        self.keyboard_listener = keyboard_listener
        self.data = data

        self.midi_listener.request_new_signal()
        self.keyboard_listener.request_new_signal()

        self.midi_listener.new_shortcut.connect(self.handle_shortcuts)
        self.keyboard_listener.new_shortcut.connect(self.handle_shortcuts)

        self.setWindowTitle(self.tr("Update Shortcuts"))
        self.setFixedSize(300, 200)  # Adjust the size as needed

        layout = QtWidgets.QVBoxLayout()

        # Add instructions as a QLabel
        instructions_label = QtWidgets.QLabel(self.tr("Press a shortcut key to update."))
        layout.addWidget(instructions_label)

        # Connect the signals from both listeners to a slot
        self.midi_listener.shortcut.connect(self.handle_shortcuts)
        self.keyboard_listener.shortcut.connect(self.handle_shortcuts)

        # Create a cancel button
        cancel_button = QtWidgets.QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.close)
        layout.addWidget(cancel_button, QtCore.Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

    @pyqtSlot(dict)
    def handle_shortcuts(self, shortcut):
        self.new_command.emit({"shortcut": shortcut, "data": self.data})
        self.midi_listener.resume_normal_operation()
        self.keyboard_listener.resume_normal_operation()
        self.accept()

    def closeEvent(self, event):
        self.midi_listener.new_shortcut.disconnect(self.handle_shortcuts)
        self.keyboard_listener.new_shortcut.disconnect(self.handle_shortcuts)
        self.midi_listener.resume_normal_operation()
        self.keyboard_listener.resume_normal_operation()
        super().closeEvent(event)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.normpath(f"UI{os.path.sep}main.ui"), self)

        self.setWindowTitle("PyNGTuber")

        self.color = (184, 205, 238)
        self.file_parameters_current = {}
        self.current_files = []
        self.json_file = os.path.normpath(f"Data{os.path.sep}parameters.json")
        self.current_json_file = os.path.normpath(f"Data{os.path.sep}current.json")
        self.settings_json_file = os.path.normpath(f"Data{os.path.sep}settings.json")

        self.keyboard_listener = KeyboardListener()
        self.keyboard_listener.shortcut.connect(self.shortcut_received)
        self.keyboard_listener.start()
        self.midi_listener = MidiListener()
        self.midi_listener.shortcut.connect(self.shortcut_received)
        self.midi_listener.start()

        try:
            with open(self.json_file, "r") as f:
                self.file_parameters_default = json.load(f)
        except FileNotFoundError:
            pass

        try:
            with open(self.json_file, "r") as f:
                self.file_parameters_current = json.load(f)
        except FileNotFoundError:
            pass

        try:
            with open(self.current_json_file, "r") as f:
                self.current_files = json.load(f)
        except FileNotFoundError:
            pass

        try:
            with open(self.settings_json_file, "r") as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            pass

        self.file_parameters_default = {os.path.normpath(key): value for key, value in self.file_parameters_default.items()}
        self.file_parameters_current = {os.path.normpath(key): value for key, value in self.file_parameters_current.items()}
        self.current_files = [os.path.normpath(i) for i in self.current_files]

        self.get_shortcuts()

        self.audio = MicrophoneVolumeWidget()
        self.audio.activeAudio.connect(self.audioStatus)
        self.audioFrame.layout().addWidget(self.audio)

        self.ImageGallery = ImageGallery(self.current_files)
        self.ImageGallery.selectionChanged.connect(self.update_viewer)
        self.scrollArea.setWidget(self.ImageGallery)

        self.SettingsGallery = SettingsToolBox()
        self.SettingsGallery.settings_changed.connect(self.saveSettings)
        self.SettingsGallery.shortcut.connect(self.dialog_shortcut)
        self.SettingsGallery.delete_shortcut.connect(self.delete_shortcut)
        self.scrollArea_2.setWidget(self.SettingsGallery)

        self.comboBox.currentIndexChanged.connect(self.setBGColor)

        self.viewer = LayeredImageViewer()
        self.viewer.loadFinishedSignal.connect(self.reboot_audio)
        self.viewerFrame.layout().addWidget(self.viewer)
        self.viewer.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.expressionSelector = ExpressionSelector("Assets")
        self.scrollArea_5.setWidget(self.expressionSelector)

        self.savedAvatars = [folder for folder in os.listdir(os.path.normpath("Models/Avatars")) if "." not in folder]
        self.modelGallery = ModelGallery(models_list=self.savedAvatars, models_type="Avatars")
        self.modelGallery.saving.connect(self.save_avatar)
        self.modelGallery.selected.connect(self.load_model)
        self.modelGallery.shortcut.connect(self.dialog_shortcut)
        self.frameModels.layout().addWidget(self.modelGallery)

        self.savedExpressions = [folder for folder in os.listdir(os.path.normpath("Models/Expressions")) if "." not in folder]
        self.expressionGallery = ModelGallery(models_list=self.savedExpressions, models_type="Expressions")
        self.expressionGallery.saving.connect(self.save_expression)
        self.expressionGallery.selected.connect(self.load_model)
        self.expressionGallery.shortcut.connect(self.dialog_shortcut)
        self.frameExpressions.layout().addWidget(self.expressionGallery)

        self.setBGColor()
        self.showUI()

        self.PNG.clicked.connect(lambda: self.export_png())

        self.saveAvatar.clicked.connect(self.save_avatar)
        self.saveExpression.clicked.connect(self.save_expression)

        self.createCategory.clicked.connect(self.CreateCategory)
        self.openFolder.clicked.connect(self.OpenAssetsFolder)

        self.tabWidget_2.currentChanged.connect(self.changePage)
        self.update_viewer(self.current_files, update_gallery=True)

    def update_settings(self):
        self.settings = {
            "volume threshold": 0,
            "scream threshold": 0,
            "delay threshold": 0,
            "background color": 0,
            "": 0
        }
        self.save_parameters_to_json()

    def delete_shortcut(self, value):
        self.file_parameters_default[value['route']]["hotkeys"] = copy.deepcopy(value["hotkeys"])
        self.file_parameters_current[value['route']]["hotkeys"] = copy.deepcopy(value["hotkeys"])
        self.save_parameters_to_json()
        self.get_shortcuts()

    def get_shortcuts(self):
        midi = []
        keyboard = []

        for root, dirs, files in os.walk("Models"):
            for filename in files:
                if filename == "data.json":
                    data_json_path = os.path.join(root, filename)
                    with open(data_json_path, 'r') as json_file:
                        data = json.load(json_file)
                        shortcut = data.get("shortcuts", None)
                        if not type(shortcut) is list:
                            if shortcut["type"] == "Keyboard":
                                keyboard.append({
                                    "path": data_json_path.replace("data", "model"),
                                    "type": "Model", "command": shortcut["command"]
                                })
                            else:
                                midi.append({
                                    "path": data_json_path.replace("data", "model"), "type": "Model",
                                    "command": mido.Message.from_dict(shortcut["command"])
                                })

        for route in self.file_parameters_current:
            if self.file_parameters_current[route]["hotkeys"]:
                if self.file_parameters_current[route]["hotkeys"]["type"] == "Keyboard":
                    keyboard.append({
                        "path": route, "type": "Asset",
                        "command": self.file_parameters_current[route]["hotkeys"]["command"]
                    })
                else:
                    midi.append(
                        {"path": route, "type": "Asset",
                         "command": mido.Message.from_dict(self.file_parameters_current[route]["hotkeys"]["command"])}
                    )

        self.midi_listener.update_shortcuts(midi)
        self.keyboard_listener.update_shortcuts(keyboard)

    def changePage(self, index):
        self.stackedWidget.setCurrentIndex(index)
        self.tabWidget.setCurrentIndex(index)
        if self.tabWidget_2.currentIndex() == 1:
            self.update_viewer(self.current_files, update_settings=True)

    def deselect_every_asset(self):
        self.current_files = []
        self.update_viewer(self.current_files, update_settings=self.tabWidget_2.currentIndex() == 1)

    def shortcut_received(self, shortcuts):
        if shortcuts["type"] == "Model":
            parts = shortcuts["path"].split(os.path.sep)
            print(parts)
            self.load_model({"name": parts[2], "type": parts[1]})
        elif shortcuts["type"] == "Asset":
            if shortcuts["path"] in self.current_files:
                self.current_files.remove(shortcuts["path"])
            else:
                self.current_files.append(shortcuts["path"])
            self.update_viewer(self.current_files, update_settings=self.tabWidget_2.currentIndex() == 1)
        else:
            print(f"Received: {shortcuts} System")

    def dialog_shortcut(self, data):
        dialog = ShortcutsDialog(midi_listener=self.midi_listener, keyboard_listener=self.keyboard_listener, data=data)
        dialog.new_command.connect(self.create_shortcuts)
        dialog.exec()

    def create_shortcuts(self, data):
        if data["data"]["type"] in ["Avatars", "Expressions"]:
            mainFolder = os.path.normpath(f"Models/{data['data']['type']}")

            used = self.find_shortcut_usages(mainFolder, data['data']['name'], data['shortcut'])
            if used:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                msg.setText(f"This shortcut already exists for another {data['data']['type'][:-1].lower()}:")
                msg.setInformativeText(
                    ",".join([
                        i.replace(
                            f"Models{os.path.sep}{data['data']['type']}{os.path.sep}", ""
                        ).replace(
                            f"{os.path.sep}data.json", "") for i in used
                    ])
                )
                msg.setWindowTitle("Model Shortcut Exists")
                msg.exec()
                return
            else:
                with open(
                        os.path.normpath(f"{mainFolder}{os.path.sep}{data['data']['name']}{os.path.sep}data.json"), 'r'
                ) as json_file:
                    old_data = json.load(json_file)
                old_data["shortcuts"] = data['shortcut']
                with open(
                        os.path.normpath(f"{mainFolder}{os.path.sep}{data['data']['name']}{os.path.sep}data.json"), 'w'
                ) as json_file:
                    json.dump(old_data, json_file, indent=4)
        if data["data"]["type"] in ["Assets"]:
            self.file_parameters_default[data['data']['value']['route']]["hotkeys"] = copy.deepcopy(data["shortcut"])
            self.file_parameters_current[data['data']['value']['route']]["hotkeys"] = copy.deepcopy(data["shortcut"])
            self.save_parameters_to_json()
            self.update_viewer(self.current_files, update_settings=True)

        self.get_shortcuts()

    def find_shortcut_usages(self, main_folder, current_folder, new_shortcut):
        usages = []
        for root, dirs, files in os.walk(main_folder):
            if root != current_folder:
                for filename in files:
                    if filename == "data.json":
                        data_json_path = os.path.join(root, filename)
                        with open(data_json_path, 'r') as json_file:
                            data = json.load(json_file)
                            shortcut = data.get("shortcuts", None)
                            if shortcut == new_shortcut:
                                usages.append(data_json_path)
        return usages

    def load_model(self, data):
        current_files = []
        with open(os.path.normpath(f"Models/{data['type']}/{data['name']}/model.json"), "r") as load_file:
            files = json.load(load_file)
            for file in files:
                self.file_parameters_current[os.path.normpath(file["route"])] = {key: value for key, value in file.items() if key != "route"}

            if data["type"] == "Avatars":
                for file in self.current_files:
                    if self.check_if_expression(file):
                        current_files.append(file)
            elif data["type"] == "Expressions":
                for file in self.current_files:
                    if not self.check_if_expression(file):
                        current_files.append(file)
            for file in files:
                current_files.append(os.path.normpath(file["route"]))

        self.update_viewer(current_files)
        # self.ImageGallery.load_images(current_files)

    def check_if_expression(self, file):
        with open(os.path.normpath("Data/expressionFolders.json"), "r") as expressions_list:
            for expression in json.load(expressions_list):
                if expression in file:
                    return True
        return False

    def CreateCategory(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter new category name:')

        if ok:
            print(str(text))

    def OpenAssetsFolder(self):
        path = os.path.normpath("Assets/")
        if os.name == "posix":
            subprocess.run(["xdg-open", path])
        elif os.name == "nt":
            subprocess.run(["explorer", path])
        else:
            print("Unsupported operating system")

    def get_folders_in_assets(self):
        folder_path = os.path.normpath("./Assets")
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            folders = [self.tr(f) for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
            return [self.tr("Select Category...")] + folders
        else:
            return [self.tr("Select Category...")]

    def save_avatar(self, model=None):
        if model is not None and model is not False:
            confirmation = QtWidgets.QMessageBox()
            confirmation.setIcon(QtWidgets.QMessageBox.Icon.Question)
            confirmation.setText("Are you sure you want to update this model?")
            confirmation.setWindowTitle("Confirmation")
            confirmation.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)

            result = confirmation.exec()

            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return

            modelName, ok = model, True
        else:
            modelName, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter new avatar name:')

        if ok:
            directory = os.path.normpath(f"Models/Avatars/{modelName}")
            if model is None or model is False:
                if os.path.exists(directory):
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                    msg.setText("This Model name already exists.")
                    msg.setInformativeText("Please choose a different model name.")
                    msg.setWindowTitle("Model Exists")
                    msg.exec()
                    return
                else:
                    os.mkdir(directory)
            temp = "savingAvatar.png"
            files = [
                file for file in self.getFiles(self.current_files)
                if not any(route in file["route"] for route in self.expressionSelector.selected_folders)
            ]
            self.image_generator(output_name=temp, method=2, savingModel=1, custom_file_list=files)
            self.save_model(directory, modelName, temp, files)
            if model is None or model is False:
                self.modelGallery.add_model(modelName)
            else:
                self.modelGallery.reload_models(
                    [folder for folder in os.listdir(f"Models{os.path.sep}Avatars") if "." not in folder])

    def save_expression(self, model=None):
        if model is not None and model is not False:
            confirmation = QtWidgets.QMessageBox()
            confirmation.setIcon(QtWidgets.QMessageBox.Icon.Question)
            confirmation.setText("Are you sure you want to update this model?")
            confirmation.setWindowTitle("Confirmation")
            confirmation.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)

            result = confirmation.exec()

            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return

            modelName, ok = model, True
        else:
            modelName, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter new expression name:')

        if ok:
            directory = os.path.normpath(f"Models{os.path.sep}Expressions{os.path.sep}{modelName}")
            if model is None or model is False:
                if os.path.exists(directory):
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                    msg.setText("This Model name already exists.")
                    msg.setInformativeText("Please choose a different model name.")
                    msg.setWindowTitle("Model Exists")
                    msg.exec()
                    return
                else:
                    os.mkdir(directory)
            temp = "savingExpression.png"
            files = [
                file for file in self.getFiles(self.current_files)
                if any(route in file["route"] for route in self.expressionSelector.selected_folders)
            ]
            self.image_generator(output_name=temp, method=2, savingModel=2, custom_file_list=files)
            self.save_model(directory, modelName, temp, files)
            if model is None or model is False:
                self.expressionGallery.add_model(modelName)
            else:
                self.expressionGallery.reload_models(
                    [folder for folder in os.listdir(f"Models{os.path.sep}Expressions") if "." not in folder])

    def save_model(self, directory, modelName, temp, files):
        self.ImageGallery.create_thumbnail(temp, custom_name=f"{directory}{os.path.sep}thumb.png")
        os.remove(temp)

        with open(os.path.normpath(f"{directory}{os.path.sep}model.json"), "w") as file:
            json.dump(files, file, indent=4)

        with open(os.path.normpath(f"{directory}{os.path.sep}data.json"), "w") as file:
            data = {
                "shortcuts": []
            }
            json.dump(data, file, indent=4)

    def export_png(self):
        method = self.PNGmethod.currentIndex()

        if method == 0:
            return

        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption=self.tr("Save File"),
            directory=str(Path.home()),
            filter=self.tr("Images (*.png)")
        )

        if fileName:
            if not fileName.lower().endswith(".png"):
                fileName += ".png"
            self.image_generator(output_name=fileName, method=method)

    def reboot_audio(self):
        self.audio.active_audio_signal = -1

    def audioStatus(self, status):
        if self.viewer.is_loaded:
            self.viewer.page().runJavaScript('''
                var elementsOpen = document.getElementsByClassName("talking_open");
                var elementsClosed = document.getElementsByClassName("talking_closed");
                var elementsScreaming = document.getElementsByClassName("talking_screaming");
                var imageWrapper = document.getElementById("image-wrapper");
        
                var opacityOpen = ''' + str(1 if status == 1 else 0) + ''';
                var opacityClosed = ''' + str(1 if status <= 0 else 0) + ''';
                var opacityScreaming = ''' + str(1 if status == 2 else 0) + ''';
        
                // Apply CSS transitions for a smooth animation to text elements
                for (var i = 0; i < elementsOpen.length; i++) {
                    elementsOpen[i].style.transition = "opacity 0.3s";
                    elementsOpen[i].style.opacity = opacityOpen;
                }
        
                for (var i = 0; i < elementsClosed.length; i++) {
                    elementsClosed[i].style.transition = "opacity 0.3s";
                    elementsClosed[i].style.opacity = opacityClosed;
                }
        
                for (var i = 0; i < elementsScreaming.length; i++) {
                    elementsScreaming[i].style.transition = "opacity 0.3s";
                    elementsScreaming[i].style.opacity = opacityScreaming;
                }
        
                // Add a CSS animation for jumping the image-wrapper
                if (''' + str(status) + ''' == 1 || ''' + str(status) + ''' == 2) {
                    imageWrapper.style.animation = "floaty 0.5s ease-in-out infinite"; 
                } else {
                    imageWrapper.style.animation = "floaty 6s ease-in-out infinite";
                }
            ''')

    def saveSettings(self, settings):
        if settings['default']:
            self.file_parameters_default[settings['value']['route']] = copy.deepcopy(settings["value"])
            self.file_parameters_default[settings['value']['route']].pop("route")
        self.file_parameters_current[settings['value']['route']] = copy.deepcopy(settings["value"])
        self.file_parameters_current[settings['value']['route']].pop("route")
        self.update_viewer(self.current_files)

    def save_parameters_to_json(self):
        with open(self.json_file, "w") as f:
            json.dump(self.file_parameters_default, f, indent=4)

        with open(self.current_json_file, "w") as f:
            json.dump(self.current_files, f, indent=4)

        with open(self.settings_json_file, "w") as f:
            json.dump(self.settings, f, indent=4)

    def image_generator(self, output_name, method=1, savingModel=0, custom_file_list=None):
        files = self.getFiles(self.current_files) if custom_file_list is None else custom_file_list
        files = [
            i for i in files
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

                    if isinstance(image, Image.Image):
                        frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
                        num_frames = len(frames)
                        middle_frame_index = num_frames // 2
                        image = frames[middle_frame_index]

                if rotation != 0:
                    image = image.rotate(rotation * -1, expand=True)

                if sizeX != image.width or sizeY != image.height:
                    image = image.resize((sizeX, sizeY))

                size_counter[(sizeX, sizeY)] += 1

                images.append((image, posZ, posX, posY))

            most_used_size = size_counter.most_common(1)[0][0]

            if images:
                images.sort(key=lambda x: x[1])

                canvas = Image.new("RGBA", (most_used_size[0], most_used_size[1]), (0, 0, 0, 0))

                for image, _, posX, posY in images:
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

                    if isinstance(image, Image.Image):
                        frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
                        num_frames = len(frames)
                        middle_frame_index = num_frames // 2
                        image = frames[middle_frame_index]

                if sizeX != image.width or sizeY != image.height:
                    image = image.resize((sizeX, sizeY))

                if rotation != 0:
                    image = image.rotate(rotation * -1, expand=True)

                center_x = self.width() // 2
                center_y = self.height() // 2

                adjusted_posX = center_x + posX - (image.width / 2)
                adjusted_posY = center_y + posY - (image.height / 2)

                images.append((image, posZ, adjusted_posX, adjusted_posY))

            if images:
                images.sort(key=lambda x: x[1])
                max_width, max_height = self.width(), self.height()
                canvas = Image.new("RGBA", (max_width, max_height))
                for image, _, posX, posY in images:
                    canvas.paste(image, (int(posX), int(posY)), image)
                canvas.save(output_name, "PNG")

    def getFiles(self, files):
        images_list = []
        for file in files:
            if file in self.file_parameters_current:
                parameters = self.file_parameters_current[file]
            else:
                image = Image.open(file)
                width, height = image.size

                parameters = {
                    "sizeX": width,
                    "sizeY": height,
                    "posX": 0,
                    "posY": 0,
                    "posZ": 40,
                    "blinking": "ignore",
                    "talking": "ignore",
                    "css": "",
                    "use_css": False,
                    "hotkeys": [],
                    "animation": [],
                    "rotation": 0,
                }

                self.file_parameters_current[file] = parameters

            images_list.append({
                "route": os.path.normpath(file),
                **parameters
            })
        return images_list

    def update_viewer(self, files=None, update_gallery=False, update_settings=False):
        images_list = self.getFiles(files)

        self.viewer.updateImages(images_list, self.color)
        if self.tabWidget_2.currentIndex() == 1:
            if self.current_files != files or update_settings:
                self.SettingsGallery.set_items(images_list)
        if update_gallery:
            self.ImageGallery.load_images(files)
        else:
            self.ImageGallery.set_buttons_checked(files)
        self.current_files = files
        self.save_parameters_to_json()

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
                self.color = "yellow"
            case 5:
                self.color = "white"
            case _:
                self.color = "#b8cdee"

        self.viewer.setColor(self.color)

    def closeEvent(self, event):
        self.audio.audio_thread.stop_stream()
        self.midi_listener.terminate()
        self.keyboard_listener.terminate()
        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    QCoreApplication.setApplicationName("PyNGtuber")

    window = MainWindow()

    window.setWindowIcon(QIcon('icon.ico'))
    window.show()

    app.exec()
