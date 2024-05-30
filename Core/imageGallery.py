
from PyQt6.QtWidgets import QWidget, QToolBox, QVBoxLayout, QPushButton, QFrame, QHBoxLayout, QSizePolicy, \
    QGridLayout, QCheckBox, QGroupBox, QMessageBox, QInputDialog, QLabel, QFileDialog, QDialog
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6.QtCore import pyqtSignal, QSize, Qt, QUrl, QTimer
from PyQt6 import uic
from PIL import Image, ImageSequence
import shutil
import json
import os


class URL_Saver(QDialog):
    new_url = pyqtSignal(dict)

    def __init__(self, exe_dir, folder_path, folder, url=None, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(exe_dir, f"UI", "url_selector.ui"), self)

        self.exe_dir = exe_dir
        self.folder_path = folder_path
        self.folder = folder
        self.url = url
        self.type = "url"

        self.browser = QWebEngineView()
        self.browser_field.layout().addWidget(self.browser)

        self.url_field.editingFinished.connect(self.update_browser)
        self.url_field.editingFinished.connect(self.update_browser)

        if self.url is not None:
            self.type = "file"
            self.url_field.setText(self.url)
            self.url_field.setReadOnly(True)

        self.save_button.clicked.connect(self.save)

    def update_browser(self):
        self.url = self.url_field.text()
        if self.type == "url":
            self.browser.load(QUrl.fromUserInput(self.url))
        else:
            self.browser.load(QUrl.fromLocalFile(self.url))

    def check_name_repeated(self, name):
        with open(os.path.join(self.folder_path, self.folder, "html_sources.json"), "r") as file:
            names = json.load(file)
        if name in list(names.keys()):
            return True
        return False

    def save(self):
        name = self.name_field.text()
        if self.check_name_repeated(name):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(f"This name already exists in this category")
            msg.setInformativeText(name)
            msg.setWindowTitle(f"Repeated name")
            msg.exec()
            return
        if name and (self.url is not None and self.url):
            self.new_url.emit({
                "name": name,
                "url": self.url,
                "folder": self.folder,
                "type": self.type,
                "route": f"$url/{self.folder}/urls/{self.type}/{self.url}"
            })
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(f"Please fill the name and URL before saving")
            msg.setInformativeText(
                f"Missing: {'Name' if not name else ''} {'URL' if self.url is None or not self.url else ''} "
            )
            msg.setWindowTitle(f"Mising data")
            msg.exec()


class ImageGallery(QToolBox):
    selectionChanged = pyqtSignal(list)

    def __init__(self, load_model, res_dir, exe_dir):
        super().__init__()
        self.selected_images = []
        self.file_paths = []
        self.last_model = None
        self.res_dir = res_dir
        self.exe_dir = exe_dir

        StyleSheet = """

        QWidget{
            background: #b8cdee;
        }

        QToolBox::tab {
            border-radius: 5px;
            text-align: center;
            color: white;
            background-color: rgba(0, 0, 0, 50);
        }

        QToolBox::tab:selected { /* italicize selected tabs */
            font: italic;
            font-weight: bold;
            background: black;
            text-align: center;
            color: white;   
        }
        
        QToolBox::tab:hover {  
            color: white;
            background-color: rgb(0, 157, 235);
        }
        
        @QScrollBar:vertical
        {
            background-color: white;
            width: 3px;
            margin: 0px 0px 0px 0px;
            border: 0px transparent white;
            border-radius: 5px;
        }
    
        QScrollBar::handle:vertical
        {
            background-color: white;
            min-height: 5px;
            border-radius: 5px;
        }
    
        QScrollBar::sub-line:vertical
        {
            margin: 0px 0px 0px 0px;
            border-image: url(:/qss_icons/rc/up_arrow_disabled.png);
            height: 0px;
            width: 0px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }
    
        QScrollBar::add-line:vertical
        {
            margin: 3px 0px 3px 0px;
            border-image: url(:/qss_icons/rc/down_arrow_disabled.png);
            height: 0px;
            width: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }
    
        QScrollBar::sub-line:vertical:hover,QScrollBar::sub-line:vertical:on
        {
            border-image: url(:/qss_icons/rc/up_arrow.png);
            height: 0px;
            width: 0px;
            subcontrol-position: top;
            subcontrol-origin: margin;
        }
    
        QScrollBar::add-line:vertical:hover, QScrollBar::add-line:vertical:on
        {
            border-image: url(:/qss_icons/rc/down_arrow.png);
            height: 0px;
            width: 0px;
            subcontrol-position: bottom;
            subcontrol-origin: margin;
        }
    
        QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical
        {
            background: none;
        }
    
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical
        {
            background: none;
        }@
        """
        self.setStyleSheet(StyleSheet)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.folder_path = os.path.join(self.res_dir, f"Assets")

    def create_thumbnail(self, input_path, max_size=(50, 50), quality=90, custom_name=None):
        file_name = os.path.basename(input_path)
        directory = os.path.dirname(input_path)

        thumbnail_folder = os.path.join(directory, "thumbs")
        os.makedirs(thumbnail_folder, exist_ok=True)

        thumbnail_path = os.path.join(thumbnail_folder, file_name.replace("gif", "png").replace("webp", "png"))
        if os.path.exists(thumbnail_path):
            return QIcon(thumbnail_path)
        try:
            if input_path.lower().endswith((".png", ".jpg", ".jpeg")):
                img = Image.open(input_path).convert("RGBA")
            elif input_path.lower().endswith((".gif", ".webp")):
                img = Image.open(input_path)

                if isinstance(img, Image.Image):
                    frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
                    num_frames = len(frames)
                    middle_frame_index = num_frames // 2
                    img = frames[middle_frame_index]
        except Exception as e:
            print(f"Error opening image: {e}")
            return None

        img_copy = img.copy()
        img_copy = img_copy.crop(img_copy.getbbox())

        width, height = img_copy.size
        max_width, max_height = max_size
        aspect_ratio = width / height

        if width > max_width or height > max_height:
            if aspect_ratio >= 1:
                new_width = max_width
                new_height = int(max_width / aspect_ratio)
            else:
                new_height = max_height
                new_width = int(max_height * aspect_ratio)

            img_copy = img_copy.resize((new_width, new_height), Image.LANCZOS)
        pixmap = QPixmap.fromImage(QImage(img_copy.tobytes("raw", "RGBA"), img_copy.size[0], img_copy.size[1], QImage.Format.Format_RGBA8888))
        pixmap.save(thumbnail_path if custom_name is None else custom_name, quality=quality)
        return QIcon(pixmap)

    def set_buttons_checked(self, load_model):
        self.selected_images = []
        self.file_paths = []
        for index in range(self.count()):
            page_widget = self.widget(index)
            if page_widget and isinstance(page_widget, QFrame):
                for i in range(page_widget.layout().count()):
                    row_layout = page_widget.layout().itemAt(i)
                    if row_layout and isinstance(row_layout, QHBoxLayout):
                        for j in range(row_layout.count()):
                            child_widget = row_layout.itemAt(j).widget()
                            if child_widget and isinstance(child_widget, QPushButton):
                                button_name = child_widget.accessibleName()

                                if button_name.startswith("Assets"):
                                    route = button_name
                                else:
                                    directory, filename = os.path.split(button_name)
                                    assets_index = directory.split(os.sep).index('Assets')
                                    route = os.path.join(*directory.split(os.sep)[assets_index:], filename)

                                child_widget.setChecked(button_name in load_model)
                                if button_name in load_model:
                                    self.list_selected(button_name, child_widget.toolTip())
                                # print(button_name, load_model)
                                # print(button_name in load_model)

    def load_images(self, load_model=None):
        self.last_model = load_model
        while self.count() > 0:
            index = 0
            widget = self.widget(index)
            if widget:
                for i in range(widget.layout().count()):
                    item = widget.layout().itemAt(i)
                    if item:
                        child_widget = item.widget()
                        if child_widget:
                            child_widget.setParent(None)
                widget.setParent(None)
            self.removeItem(index)

        if not os.path.exists(self.folder_path) and os.path.isdir(self.folder_path):
            page_widget = QFrame()
            page_layout = QVBoxLayout(page_widget)
            page_layout.setContentsMargins(0, 0, 6, 0)
            page_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            page_layout.addWidget(QLabel("Assets Folder Not Found"))
            folder_name = os.path.basename("Assets Folder Not Found")
            self.addItem(page_widget, folder_name.title())
            return

        for subdir, dirs, files in os.walk(self.folder_path):
            if "thumb" not in subdir.lower():
                folder_name = os.path.basename(subdir)
                if folder_name != "Assets":
                    page_widget = QFrame()

                    page_layout = QVBoxLayout(page_widget)
                    page_layout.setContentsMargins(0, 0, 6, 0)

                    add_asset_button = QPushButton("Add new asset")
                    add_asset_button.clicked.connect(self.add_asset)
                    add_asset_button.setIcon(QIcon("Icons/in-magnifiction-mobile-svgrepo-com.svg"))
                    add_asset_button.setIconSize(QSize(30, 30))
                    add_asset_button.setAccessibleName(folder_name)
                    page_layout.addWidget(add_asset_button)

                    row_layout = QHBoxLayout()
                    row_layout.setContentsMargins(0, 0, 0, 0)
                    page_layout.addLayout(row_layout)
                    column_count = 0
                    fileCount = 1

                    if not os.path.isfile(os.path.join(self.folder_path, folder_name, "html_sources.json")):
                        with open(os.path.join(self.folder_path, folder_name, "html_sources.json"), "w") as file:
                            json.dump({}, file, indent=4, ensure_ascii=False)

                    for file in files:
                        if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                            button_name = str(os.path.join(subdir, file)).split(f"{os.path.sep}..{os.path.sep}")[-1]

                            if button_name.startswith("Assets"):
                                route = button_name
                            else:
                                directory, filename = os.path.split(button_name)
                                assets_index = directory.split(os.sep).index('Assets')
                                route = os.path.join(*directory.split(os.sep)[assets_index:], filename)

                            item = QPushButton()
                            item.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
                            item.setIcon(self.create_thumbnail(os.path.join(subdir, file)))
                            item.setIconSize(QSize(20, 30) if os.name == 'nt' else QSize(30, 40))
                            item.setAccessibleName(route)
                            item.setToolTip(str(route))
                            item.setCheckable(True)
                            item.setStyleSheet("QPushButton:checked{background-color: red !important}")
                            if load_model is not None:
                                checked = button_name in load_model
                                item.setChecked(checked)
                                if checked:
                                    self.list_selected(route, str(route))

                            item.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                            item.customContextMenuRequested.connect(self.delete_file)

                            item.clicked.connect(self.update_selected)
                            row_layout.addWidget(item)
                            column_count += 1
                            fileCount += 1

                            if column_count == 6:
                                row_layout = QHBoxLayout()
                                page_layout.addLayout(row_layout)
                                column_count = 0

                        elif file.lower().endswith((".json")):
                            with open(os.path.join(subdir, file), "r") as html_sources_file:
                                html_sources = json.load(html_sources_file)
                            for html_source in html_sources:
                                button_name = html_source
                                route = html_sources[html_source]["route"]

                                item = QPushButton(button_name)
                                item.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
                                item.setAccessibleName(route)
                                item.setToolTip(route)
                                item.setCheckable(True)
                                item.setStyleSheet("QPushButton:checked{background-color: red !important}")

                                if load_model is not None:
                                    checked = (
                                                  html_sources[html_source]["route"].replace("/file//", "/file/")
                                                  if route.startswith("$url") else
                                                  html_sources[html_source]
                                              ) in load_model
                                    item.setChecked(checked)
                                    if checked:
                                        self.list_selected(route, route)

                                item.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                                item.customContextMenuRequested.connect(self.delete_file)

                                item.clicked.connect(self.update_selected)
                                fileCount += 1
                                page_layout.addWidget(item)
                    if fileCount > 0:
                        self.addItem(page_widget, folder_name.title())

    def get_unique_filename(self, folder_path, folder_name, extension):
        base_filename = f"{folder_name}.{extension}"
        full_path = os.path.join(folder_path, folder_name, base_filename)
        counter = 1

        while os.path.exists(full_path):
            base_filename = f"{folder_name}_{counter:03d}.{extension}"
            full_path = os.path.join(folder_path, folder_name, base_filename)
            counter += 1

        return full_path

    def add_asset(self):
        sender = self.sender()
        folder = sender.accessibleName()
        # print(folder)

        asset_type = QMessageBox()
        asset_type.setIcon(QMessageBox.Icon.Question)
        asset_type.setText("What kind of asset you want to add?")
        asset_type.setWindowTitle("Type of asset")
        asset_type.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.Apply |
            # QMessageBox.StandardButton.Ok |
            QMessageBox.StandardButton.Cancel
        )

        buttonY = asset_type.button(QMessageBox.StandardButton.Yes)
        buttonY.setText('Image File')
        buttonN = asset_type.button(QMessageBox.StandardButton.Apply)
        buttonN.setText('HTML File')
        # buttonN = asset_type.button(QMessageBox.StandardButton.Ok)
        # buttonN.setText('URL')

        result = asset_type.exec()

        if result == QMessageBox.StandardButton.Yes:
            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
            file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif *.webp)")
            files, _ = file_dialog.getOpenFileNames(None, "Select Images", "", "Images (*.png *.jpg *.jpeg *.gif *.webp)")
            if files:
                for file in files:
                    extension = os.path.splitext(file)[1].lstrip('.').lower()
                    unique_filename = self.get_unique_filename(self.folder_path, folder, extension)
                    shutil.copy(file, unique_filename)
        elif result == QMessageBox.StandardButton.Apply:
            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
            file_dialog.setNameFilter("HTML Files (*.html)")
            files, _ = file_dialog.getOpenFileNames(None, "Select Images", "", "HTML Files (*.html)")
            if files:
                for file in files:
                    self.select_url(folder, file)

        elif result == QMessageBox.StandardButton.Ok:
            self.select_url(folder)
        else:
            return

        self.load_images(self.last_model)

    def select_url(self, folder, url=None):
        twitch_dialog = URL_Saver(exe_dir=self.exe_dir, folder_path=self.folder_path, folder=folder, url=url)
        twitch_dialog.new_url.connect(self.save_url)
        twitch_dialog.exec()

    def save_url(self, data):
        with open(os.path.join(self.folder_path, data["folder"], "html_sources.json"), "r") as html_sources_file:
            html_sources = json.load(html_sources_file)

        html_sources[data["name"]] = data
        with open(os.path.join(self.folder_path, data["folder"], "html_sources.json"), "w") as file:
            json.dump(html_sources, file, indent=4, ensure_ascii=False)

    def list_selected(self, value, tooltip):
        self.selected_images.append(value)
        self.file_paths.append(tooltip)

    def update_selected(self):
        sender = self.sender()
        accessibleName = sender.accessibleName()
        toolTip = sender.toolTip()
        if sender.isChecked():
            try:
                self.selected_images.append(json.loads(accessibleName))
            except BaseException:
                self.selected_images.append(os.path.normpath(accessibleName))
            self.file_paths.append(os.path.normpath(toolTip))
        else:
            try:
                self.selected_images.remove(json.loads(accessibleName))
            except BaseException:
                self.selected_images.remove(os.path.normpath(accessibleName))
            self.file_paths.remove(os.path.normpath(toolTip))
        self.selectionChanged.emit(self.selected_images)

    def get_selected_files(self):
        self.file_paths = []
        self.selected_images = []

        for index in range(self.count()):
            page_widget = self.widget(index)
            for button in page_widget.findChildren(QPushButton):
                if button.isChecked():
                    try:
                        self.selected_images.append(json.loads(button.accessibleName()))
                    except BaseException:
                        self.selected_images.append(os.path.normpath(button.accessibleName()))
                    self.file_paths.append(os.path.normpath(button.toolTip()))
        self.selectionChanged.emit(self.selected_images)
        return self.file_paths

    def delete_file(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Icon.Question)
        confirmation.setText("Are you sure you want to delete this asset?")
        confirmation.setWindowTitle("Confirmation")
        confirmation.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        result = confirmation.exec()

        sender = self.sender()
        path = sender.toolTip()
        button_text = sender.text()

        if result == QMessageBox.StandardButton.Yes:
            try:
                if path.startswith("$url"):
                    with open(os.path.join(self.res_dir, "Assets", path.split("/")[1], "html_sources.json"), "r") as html_sources_file:
                        html_sources = json.load(html_sources_file)

                    result = {}
                    for i in html_sources:
                        if not path == html_sources[i]["route"]:
                            result[i] = html_sources[i]

                    with open(os.path.join(self.res_dir, "Assets", path.split("/")[1], "html_sources.json"), "w") as html_sources_file:
                        json.dump(result, html_sources_file, indent=4, ensure_ascii=False)
                else:
                    os.remove(os.path.join(self.res_dir, path))
                index = self.currentIndex()
                self.load_images(self.last_model)
                self.setCurrentIndex(index)
                self.get_selected_files()
            except Exception as e:
                print(f"Error deleting file: {str(e)}")


class ModelItem(QGroupBox):
    selected = pyqtSignal(dict)
    shortcut = pyqtSignal(dict)
    deleted = pyqtSignal()
    saving = pyqtSignal(str)

    def __init__(self, modelName, modelType, exe_dir, res_dir):
        super().__init__()
        uic.loadUi(os.path.join(exe_dir, f"UI", "avatar.ui"), self)
        self.modelName = modelName
        self.modelType = modelType
        self.res_dir = res_dir

        self.avatarButton.clicked.connect(self.selectedModel)
        self.avatarButton.setToolTip(f"Load {self.modelType}")

        self.deleteButton.clicked.connect(self.delete_model)
        self.renameButton.clicked.connect(self.rename_model)
        self.hotkeyButton.clicked.connect(self.shortcutChange)
        self.save.clicked.connect(self.saveChanges)

        self.shortcuts = []

        self.setup()
        self.frame_3.hide()
        self.frame_2.hide()

    def saveChanges(self):
        self.saving.emit(self.modelName)

    def selectedModel(self):
        self.selected.emit({"name": self.modelName, "type": self.modelType})

    def shortcutChange(self):
        self.shortcut.emit({"name": self.modelName, "type": self.modelType, "value": {"hotkeys": self.shortcuts}})

    def enterEvent(self, event):
        self.frame_3.show()
        self.frame_2.show()

    def leaveEvent(self, event):
        self.frame_3.hide()
        self.frame_2.hide()

    def setup(self):
        self.setTitle(self.modelName)
        self.avatarButton.setIcon(
            QIcon(os.path.join(self.res_dir, "Models", self.modelType, self.modelName, "thumb.png"))
        )
        self.show_shortcut()

    def show_shortcut(self):
        with open(os.path.join(self.res_dir, "Models", self.modelType, self.modelName, "data.json"),
                  "r") as data_file:
            self.shortcuts = json.load(data_file)["shortcuts"]

    def delete_model(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Icon.Question)
        confirmation.setText("Are you sure you want to delete this model?")
        confirmation.setWindowTitle("Confirmation")
        confirmation.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        result = confirmation.exec()

        if result == QMessageBox.StandardButton.Yes:
            shutil.rmtree(os.path.join(self.res_dir, "Models", self.modelType, self.modelName))
            self.deleted.emit()

    def rename_model(self):
        modelName, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter new model name:')

        if ok:
            os.rename(
                os.path.join("Models", self.modelType, self.modelName),
                os.path.join("Models", self.modelType, modelName)
            )
            self.setTitle(modelName)
            self.modelName = modelName


class ModelGallery(QWidget):
    selected = pyqtSignal(dict)
    shortcut = pyqtSignal(dict)
    saving = pyqtSignal(str)

    def __init__(self, models_list, models_type, exe_dir, res_dir):
        super().__init__()
        self.models_list = models_list
        self.models_type = models_type
        self.exe_dir = exe_dir
        self.res_dir = res_dir
        layout = QGridLayout()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.setLayout(layout)

        self.load_models()

    def reload_models(self, new_list):
        self.models_list = new_list
        self.clearLayout()  # Clear the layout before reloading models
        self.load_models()

    def clearLayout(self):
        for _ in reversed(range(self.layout().count())):
            self.layout().itemAt(_).widget().setParent(None)

    def load_models(self):
        for idx, model in enumerate(self.models_list):
            row = idx // 2  # Calculate the row index
            col = idx % 2   # Calculate the column index
            self.add_model(model, row, col)

    def add_model(self, model, row, col):
        model_item = ModelItem(model, self.models_type, self.exe_dir, self.res_dir)

        model_item.selected.connect(self.selected.emit)
        model_item.deleted.connect(self.model_deleted)
        model_item.shortcut.connect(self.shortcut.emit)
        model_item.saving.connect(self.saving.emit)

        self.layout().addWidget(model_item, row, col, 1, 1)

    def model_deleted(self):
        self.sender().setParent(None)


class ExpressionSelector(QWidget):
    def __init__(self, folder_path):
        super().__init__()

        self.selected_folders = []

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        folders = [folder for folder in os.listdir(folder_path) if "." not in folder]
        self.checkboxes = {}
        row = 0

        for i, folder in enumerate(folders):
            checkbox = QCheckBox(folder)
            checkbox.setStyleSheet("*{font-size: 8px}")
            checkbox.toggled.connect(self.save_to_json)
            self.checkboxes[folder] = checkbox

            col = i % 2
            layout.addWidget(checkbox, row, col)
            if col == 1:
                row += 1

        self.setLayout(layout)
        self.load_from_json()

    def save_to_json(self, state):
        sender = self.sender()
        if state is True:
            self.selected_folders.append(sender.text())
        else:
            if sender.text() in self.selected_folders:
                self.selected_folders.remove(sender.text())

        if self.selected_folders:
            with open("Data/expressionFolders.json", "w") as json_file:
                json.dump(self.selected_folders, json_file, indent=4)

    def load_from_json(self):
        try:
            with open("Data/expressionFolders.json", "r") as json_file:
                self.selected_folders = json.load(json_file)
                for folder, checkbox in self.checkboxes.items():
                    if folder in self.selected_folders:
                        checkbox.blockSignals(True)
                        checkbox.setChecked(True)
                        checkbox.blockSignals(False)
        except BaseException as e:
            print(e)
