
from PyQt6.QtWidgets import QWidget, QToolBox, QVBoxLayout, QPushButton, QFrame, QHBoxLayout, QSizePolicy, QGridLayout, QCheckBox, QGroupBox, QMessageBox, QInputDialog, QLabel
from PyQt6.QtGui import QIcon, QPixmap, QImage
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6 import uic
from PIL import Image
import shutil
import json
import os


class ImageGallery(QToolBox):
    selectionChanged = pyqtSignal(list)

    def __init__(self, load_model):
        super().__init__()
        
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
        # self.setVerticalPolicy(QSizePolicy.verticalPolicy.MinimumExpanding)
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
        self.folder_path = os.path.join(script_dir, "../Assets")

        self.load_images()

    def create_thumbnail(self, input_path, max_size=(50, 50), quality=90, custom_name=None):
        # Extract the file name and directory from the input path
        file_name = os.path.basename(input_path)
        directory = os.path.dirname(input_path)

        # Define the destination folder for thumbnails
        thumbnail_folder = os.path.join(directory, "thumbs")
        os.makedirs(thumbnail_folder, exist_ok=True)  # Create the Thumbnails folder if it doesn't exist

        # Define the thumbnail path
        thumbnail_path = os.path.join(thumbnail_folder, file_name.replace("gif", "png").replace("webp", "png"))

        # Check if a thumbnail already exists
        if os.path.exists(thumbnail_path):
            # Thumbnail already exists, load and return it as QIcon
            return QIcon(thumbnail_path)

        # Open the image using Pillow
        try:
            img = Image.open(input_path).convert("RGBA")
        except Exception as e:
            print(f"Error opening image: {e}")
            return None

        # Create a copy of the original image
        img_copy = img.copy()

        # Crop the image by removing fully transparent rows and columns
        img_copy = img_copy.crop(img_copy.getbbox())

        # Calculate the new size while maintaining the aspect ratio
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

            # Resize the image with Lanczos resampling
            img_copy = img_copy.resize((new_width, new_height), Image.LANCZOS)

        # Convert the cropped and resized image to a QPixmap
        pixmap = QPixmap.fromImage(QImage(img_copy.tobytes("raw", "RGBA"), img_copy.size[0], img_copy.size[1], QImage.Format.Format_RGBA8888))

        # Save the QPixmap as the thumbnail with compression
        pixmap.save(thumbnail_path if custom_name is None else custom_name, quality=quality)
        print(f"Created thumbnail: {thumbnail_path}")

        # Return the created QIcon
        return QIcon(pixmap)

    def load_images(self, load_model=None):
        while self.count() > 0:
            index = 0
            widget = self.widget(index)  # Get the associated widget
            if widget:
                # Iterate through and remove all child widgets
                for i in range(widget.layout().count()):
                    child_widget = widget.layout().itemAt(i).widget()
                    if child_widget:
                        child_widget.setParent(None)  # Set the child widget's parent to None

                widget.setParent(None)  # Set the main widget's parent to None
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
                # Create a widget for each subfolder
                page_widget = QFrame()
                # page_widget.setMaximumHeight(400)
                # page_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
                page_layout = QVBoxLayout(page_widget)
                page_layout.setContentsMargins(0, 0, 6, 0)

                row_layout = QHBoxLayout()
                row_layout.setContentsMargins(0, 0, 0, 0)
                page_layout.addLayout(row_layout)
                column_count = 0

                fileCount = 0
                for file in files:
                    # Check if the file is an image (you can add more image formats)
                    if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                        button_name = str(os.path.join(subdir, file)).split("/../")[-1]
                        item = QPushButton()
                        item.setIcon(self.create_thumbnail(os.path.join(subdir, file)))
                        item.setIconSize(QSize(30, 30))
                        item.setAccessibleName(button_name)
                        item.setCheckable(True)
                        if load_model is not None:
                            item.setChecked(button_name in load_model)
                        item.clicked.connect(self.handle_button_click)
                        row_layout.addWidget(item)
                        column_count += 1
                        fileCount += 1

                        # Start a new row after 3 columns
                        if column_count == 4:
                            row_layout = QHBoxLayout()
                            page_layout.addLayout(row_layout)
                            column_count = 0

                if fileCount > 0:
                    folder_name = os.path.basename(subdir)
                    self.addItem(page_widget, folder_name.title())  # Set folder name as the page title dynamically

    def handle_button_click(self):
        selected_images = []

        for index in range(self.count()):
            page_widget = self.widget(index)
            for button in page_widget.findChildren(QPushButton):
                if button.isChecked():
                    selected_images.append(button.accessibleName())

        # Emit the selectionChanged signal with the list of selected images
        self.selectionChanged.emit(selected_images)


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
            # Perform the deletion here
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
        row = 0  # Initialize the row variable

        for i, folder in enumerate(folders):
            checkbox = QCheckBox(folder)
            checkbox.setStyleSheet("*{font-size: 8px}")
            checkbox.toggled.connect(self.save_to_json)
            self.checkboxes[folder] = checkbox

            # Calculate the column number based on whether i is even or odd
            col = i % 2

            # Add the checkbox to the grid layout at the specified row and column
            layout.addWidget(checkbox, row, col)

            # If the current checkbox is in the second column, increment the row
            if col == 1:
                row += 1

        self.setLayout(layout)
        # Load saved data and preselect checkboxes
        self.load_from_json()

    def save_to_json(self, state):
        sender = self.sender()
        if state is True:  # Qt.Checked
            self.selected_folders.append(sender.text())
        else:  # Qt.Unchecked
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
