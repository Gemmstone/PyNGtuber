import sys
import os
import pygame
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPainter

class ImageSprite(pygame.sprite.Sprite):
    def __init__(self, image_path, position):
        super().__init__()
        self.image = pygame.image.load(image_path)
        self.rect = self.image.get_rect()
        self.rect.topleft = position
        self.shared_animation = None
        self.individual_animation = None

    def set_shared_animation(self, animation_data):
        self.shared_animation = animation_data

    def set_individual_animation(self, animation_data):
        self.individual_animation = animation_data

    def update(self):
        if self.shared_animation:
            # Apply shared animation
            self.rect.move_ip(*self.shared_animation["movement"])

        if self.individual_animation:
            # Apply individual animation
            self.rect.move_ip(*self.individual_animation["movement"])

class LayeredImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layered Image Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.image_sprites = []  # List to store image sprites
        self.shared_animation = None  # Shared animation for all images
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_sprites)
        self.load_button = QPushButton("Load Images", self)
        self.load_button.clicked.connect(self.load_images)

        layout = QVBoxLayout()
        layout.addWidget(self.load_button)
        self.setLayout(layout)

    def load_images(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Images (*.png *.gif *.apng)")
        file_paths, _ = file_dialog.getOpenFileNames(self, "Select Images", "", options=options)

        if file_paths:
            # Clear existing sprites
            self.image_sprites = []

            # Load images and create sprites
            for i, file_path in enumerate(file_paths):
                sprite = ImageSprite(file_path, (i * 100, i * 100))
                self.image_sprites.append(sprite)

            # Load shared animation from JSON
            shared_animation_path = "shared_animation.json"
            if os.path.exists(shared_animation_path):
                with open(shared_animation_path, "r") as json_file:
                    self.shared_animation = json.load(json_file)

            # Start the timer to update the sprites
            self.timer.start(100)  # Adjust the frame rate as needed

    def update_sprites(self):
        for sprite in self.image_sprites:
            sprite.update()

        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        for sprite in self.image_sprites:
            painter.drawImage(sprite.rect, sprite.image)

    def closeEvent(self, event):
        # Save shared animation to JSON
        shared_animation_path = "shared_animation.json"
        if self.shared_animation:
            with open(shared_animation_path, "w") as json_file:
                json.dump(self.shared_animation, json_file)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = LayeredImageViewer()
    viewer.show()

    sys.exit(app.exec_())
