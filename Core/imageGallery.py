import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QToolBox, QVBoxLayout, QPushButton, QFrame, QHBoxLayout, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QSize

class ImageGallery(QToolBox):
    selectionChanged = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
        folder_path = os.path.join(script_dir, "../Assets")

        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            self.load_images(folder_path)
        else:
            self.addItem(QWidget(), "Assets Folder Not Found")  # Add a placeholder page if the folder doesn't exist

    def load_images(self, folder_path):
        for subdir, dirs, files in os.walk(folder_path):
            # Create a widget for each subfolder
            page_widget = QFrame()
            page_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
            page_layout = QVBoxLayout(page_widget)

            row_layout = QHBoxLayout()
            page_layout.addLayout(row_layout)
            column_count = 0

            fileCount = 0
            for file in files:
                # Check if the file is an image (you can add more image formats)
                if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                    item = QPushButton()
                    item.setIcon(QIcon(os.path.join(subdir, file)))
                    item.setIconSize(QSize(50, 50))
                    item.setCheckable(True)
                    item.clicked.connect(self.handle_button_click)
                    row_layout.addWidget(item)
                    column_count += 1
                    fileCount += 1

                    # Start a new row after 3 columns
                    if column_count == 3:
                        row_layout = QHBoxLayout()
                        page_layout.addLayout(row_layout)
                        column_count = 0

            if fileCount > 0:
                folder_name = os.path.basename(subdir)
                self.addItem(page_widget, folder_name)  # Set folder name as the page title dynamically

    def handle_button_click(self):
        selected_images = []

        for index in range(self.count()):
            page_widget = self.widget(index)
            for button in page_widget.findChildren(QPushButton):
                if button.isChecked():
                    selected_images.append(button.text())

        # Emit the selectionChanged signal with the list of selected images
        self.selectionChanged.emit(selected_images)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gallery = ImageGallery()
    gallery.show()
    sys.exit(app.exec_())
