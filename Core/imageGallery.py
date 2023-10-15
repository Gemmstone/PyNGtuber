
from PyQt6.QtWidgets import QWidget, QToolBox, QVBoxLayout, QPushButton, QFrame, QHBoxLayout, QSizePolicy, \
    QGridLayout, QCheckBox, QGroupBox, QMessageBox, QInputDialog, QLabel, QFileDialog, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6.QtCore import pyqtSignal, QSize, Qt
from PyQt6.QtGui import QAction
from PyQt6 import uic
from PIL import Image
import shutil
import json
import os


class ImageGallery(QToolBox):
    selectionChanged = pyqtSignal(list)

    def __init__(self, load_model):
        super().__init__()
        self.last_model = None

        StyleSheet = """

        QWidget{
            background: #b8cdee;
        }

        QToolBox::tab {
            background: #009deb;
            border-radius: 5px;
            text-align: center;
            color: black;
        }
        
        /* 
        QToolBox::tab:first {
            background: #4ade00;
            border-radius: 5px;
            color: black;
        }

        QToolBox::tab:last {
            background: #f95300;
            border-radius: 5px;
            color: black;
        }
        */

        QToolBox::tab:selected { /* italicize selected tabs */
            font: italic;
            font-weight: bold;
            background: pink;
            text-align: center;
            color: black;   
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
        self.folder_path = os.path.join(script_dir, f"..{os.path.sep}Assets")

    def create_thumbnail(self, input_path, max_size=(50, 50), quality=90, custom_name=None):
        file_name = os.path.basename(input_path)
        directory = os.path.dirname(input_path)

        thumbnail_folder = os.path.join(directory, "thumbs")
        os.makedirs(thumbnail_folder, exist_ok=True)

        thumbnail_path = os.path.join(thumbnail_folder, file_name.replace("gif", "png").replace("webp", "png"))
        if os.path.exists(thumbnail_path):
            return QIcon(thumbnail_path)

        try:
            img = Image.open(input_path).convert("RGBA")
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
                                child_widget.setChecked(button_name in load_model)

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

                    for file in files:
                        if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                            button_name = str(os.path.join(subdir, file)).split(f"{os.path.sep}..{os.path.sep}")[-1]
                            item = QPushButton()
                            item.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
                            item.setIcon(self.create_thumbnail(os.path.join(subdir, file)))
                            item.setIconSize(QSize(20, 30) if os.name == 'nt' else QSize(30, 40))
                            item.setAccessibleName(button_name)
                            item.setToolTip(str(os.path.join(subdir, file)))
                            item.setCheckable(True)
                            item.setStyleSheet("QPushButton:checked{background-color: red !important}")
                            if load_model is not None:
                                item.setChecked(button_name in load_model)

                            item.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                            item.customContextMenuRequested.connect(self.delete_file)

                            item.clicked.connect(self.get_selected_files)
                            row_layout.addWidget(item)
                            column_count += 1
                            fileCount += 1

                            if column_count == 4:
                                row_layout = QHBoxLayout()
                                page_layout.addLayout(row_layout)
                                column_count = 0

                    if fileCount > 0:
                        self.addItem(page_widget, folder_name.title())

    def add_asset(self):
        sender = self.sender()
        folder = sender.accessibleName()
        print(folder)

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.gif *.webp)")
        files, _ = file_dialog.getOpenFileNames(None, "Select Images", "", "Images (*.png *.jpg *.jpeg *.gif *.webp)")

        if files:
            for file in files:
                print(file)

            self.load_images(self.last_model)

    def get_selected_files(self):
        file_paths = []
        selected_images = []

        for index in range(self.count()):
            page_widget = self.widget(index)
            for button in page_widget.findChildren(QPushButton):
                if button.isChecked():
                    selected_images.append(os.path.normpath(button.accessibleName()))
                    file_paths.append(os.path.normpath(button.toolTip()))

        self.selectionChanged.emit(selected_images)
        return file_paths

    def delete_file(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Icon.Question)
        confirmation.setText("Are you sure you want to delete this asset?")
        confirmation.setWindowTitle("Confirmation")
        confirmation.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        result = confirmation.exec()

        path = self.sender().toolTip()
        if result == QMessageBox.StandardButton.Yes:
            try:
                os.remove(path)
                self.load_images(self.last_model)
            except Exception as e:
                print(f"Error deleting file: {str(e)}")


class ModelItem(QGroupBox):
    selected = pyqtSignal(dict)
    shortcut = pyqtSignal(dict)
    deleted = pyqtSignal()
    saving = pyqtSignal(str)

    def __init__(self, modelName, modelType):
        super().__init__()
        uic.loadUi("UI/avatar.ui", self)
        self.modelName = modelName
        self.modelType = modelType

        self.avatarButton.clicked.connect(self.selectedModel)
        self.avatarButton.setToolTip(f"Load {self.modelType}")

        self.deleteButton.clicked.connect(self.delete_model)
        self.renameButton.clicked.connect(self.rename_model)
        self.hotkeyButton.clicked.connect(self.shortcutChange)
        self.save.clicked.connect(self.saveChanges)

        self.setup()
        self.frame_3.hide()
        self.frame_2.hide()

    def saveChanges(self):
        self.saving.emit(self.modelName)

    def selectedModel(self):
        self.selected.emit({"name": self.modelName, "type": self.modelType})

    def shortcutChange(self):
        self.shortcut.emit({"name": self.modelName, "type": self.modelType})

    def enterEvent(self, event):
        self.frame_3.show()
        self.frame_2.show()

    def leaveEvent(self, event):
        self.frame_3.hide()
        self.frame_2.hide()

    def setup(self):
        self.setTitle(self.modelName)
        self.avatarButton.setIcon(QIcon(f"Models/{self.modelType}/{self.modelName}/thumb.png"))

    def delete_model(self):
        confirmation = QMessageBox()
        confirmation.setIcon(QMessageBox.Icon.Question)
        confirmation.setText("Are you sure you want to delete this model?")
        confirmation.setWindowTitle("Confirmation")
        confirmation.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        result = confirmation.exec()

        if result == QMessageBox.StandardButton.Yes:
            shutil.rmtree(f"Models/{self.modelType}/{self.modelName}")
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

    def __init__(self, models_list, models_type):
        super().__init__()
        self.models_list = models_list
        self.models_type = models_type
        layout = QVBoxLayout()

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.setLayout(layout)

        self.load_models()

    def reload_models(self, new_list):
        self.models_list = new_list
        for _ in reversed(range(self.layout().count())):
            self.layout().itemAt(_).widget().setParent(None)
        self.load_models()

    def load_models(self):
        for model in self.models_list:
            self.add_model(model)

    def add_model(self, model):
        model_item = ModelItem(model, self.models_type)

        model_item.selected.connect(self.selected.emit)
        model_item.deleted.connect(self.model_deleted)
        model_item.shortcut.connect(self.shortcut.emit)
        model_item.saving.connect(self.saving.emit)

        self.layout().addWidget(model_item)

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
                        checkbox.setChecked(True)
        except BaseException as e:
            print(e)
