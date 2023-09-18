import sys
import json
import os
from PyQt5 import QtCore, QtGui, QtWidgets


class LayeredImageViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.models_data = []  # List to store model data
        self.background_color = (0, 255, 0)  # Default background color (Green)

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.initUI()

        self.model_list.setCurrentRow(0)  # Select the first model
        try:
            self.updateLayerList(self.models_data[0])  # Update the layer list for the first model
        except IndexError:
            pass

    def initUI(self):
        self.setWindowTitle('PyNGtuber')
        self.setGeometry(100, 100, 800, 600)

        # Create a central widget
        self.central_widget_ = QtWidgets.QWidget()

        self.setCentralWidget(self.central_widget_)

        # Create a horizontal layout for the central widget
        layout = QtWidgets.QHBoxLayout()
        self.central_widget_.setLayout(layout)

        # Create a QWidget for the left menu and buttons
        left_menu_widget = QtWidgets.QWidget()
        left_menu_layout = QtWidgets.QVBoxLayout()

        # Create a QListWidget for selecting models
        self.model_list = QtWidgets.QListWidget()
        self.model_list.itemDoubleClicked.connect(self.renameModel)
        self.model_list.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        left_menu_layout.addWidget(self.model_list)

        # Create a QPushButton to add a new empty model or clone the selected model
        self.add_model_button = QtWidgets.QPushButton('Add Model')
        self.add_model_button.clicked.connect(self.addEmptyModelOrClone)
        left_menu_layout.addWidget(self.add_model_button)

        # Create a QPushButton to delete the selected model
        self.delete_model_button = QtWidgets.QPushButton('Delete Model')
        self.delete_model_button.clicked.connect(self.deleteSelectedModel)
        left_menu_layout.addWidget(self.delete_model_button)

        # Create a QComboBox to select the canvas background color (chroma key color)
        self.bg_color_combo = QtWidgets.QComboBox()
        self.bg_color_combo.addItem('Green (Default)')
        self.bg_color_combo.addItem('Cyan')
        self.bg_color_combo.addItem('Magenta')
        self.bg_color_combo.addItem('Transparent (Might not work)')
        self.bg_color_combo.activated.connect(self.setCanvasBackgroundColor)
        self.bg_color_combo.setCurrentIndex(0)  # Set green as the default
        left_menu_layout.addWidget(self.bg_color_combo)

        # Add the left menu to the left_menu_widget
        left_menu_widget.setLayout(left_menu_layout)

        # Create a QWidget for the canvas and layer list
        canvas_and_layers_widget = QtWidgets.QWidget()
        canvas_and_layers_layout = QtWidgets.QVBoxLayout()

        # Create a QWidget for the right layer settings
        right_widget = QtWidgets.QWidget()
        right_widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        right_layout = QtWidgets.QVBoxLayout()

        # Create a QPushButton to add a picture as a layer
        self.add_picture_button = QtWidgets.QPushButton('Add Picture as Layer')
        self.add_picture_button.clicked.connect(self.addPicture)
        right_layout.addWidget(self.add_picture_button)

        # Create a QListWidget for listing layers
        self.layer_list = QtWidgets.QListWidget()
        self.layer_list.itemDoubleClicked.connect(self.renameLayer)
        self.layer_list.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        right_layout.addWidget(self.layer_list)

        # Create a QGraphicsView widget to display the images
        self.view = QtWidgets.QGraphicsView()
        self.scene = QtWidgets.QGraphicsScene()
        self.view.setScene(self.scene)  # Set the scene for the view
        self.view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        canvas_and_layers_layout.addWidget(self.view)

        # Add the canvas and layer list to the canvas_and_layers_widget
        canvas_and_layers_widget.setLayout(canvas_and_layers_layout)

        # Create a QWidget for layer settings
        self.layer_settings_widget = QtWidgets.QWidget()
        self.layer_settings_layout = QtWidgets.QFormLayout()
        self.layer_settings_widget.setLayout(self.layer_settings_layout)

        # Create a QLabel to show layer information
        self.layer_info_label = QtWidgets.QLabel()
        self.layer_settings_layout.addRow('Layer Info:', self.layer_info_label)

        # Create a QLabel to show the thumbnail of the selected layer
        self.layer_thumbnail_label = QtWidgets.QLabel()
        self.layer_thumbnail_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layer_settings_layout.addRow('Thumbnail:', self.layer_thumbnail_label)

        # Create sliders and spin boxes for layer settings
        self.layer_opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.layer_opacity_slider.setRange(0, 100)
        self.layer_opacity_slider.valueChanged.connect(self.updateLayerOpacity)
        self.layer_settings_layout.addRow('Opacity:', self.layer_opacity_slider)

        self.layer_x_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.layer_x_slider.setRange(0, 800)  # Adjust the range as needed
        self.layer_x_slider.valueChanged.connect(self.updateLayerPositionX)
        self.layer_settings_layout.addRow('X Position:', self.layer_x_slider)

        self.layer_y_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.layer_y_slider.setRange(0, 600)  # Adjust the range as needed
        self.layer_y_slider.valueChanged.connect(self.updateLayerPositionY)
        self.layer_settings_layout.addRow('Y Position:', self.layer_y_slider)

        self.layer_z_spinbox = QtWidgets.QSpinBox()
        self.layer_z_spinbox.setRange(0, 1000)  # Adjust the range as needed
        self.layer_z_spinbox.valueChanged.connect(self.updateLayerZ)
        self.layer_settings_layout.addRow('Z Position:', self.layer_z_spinbox)

        # Create a QPushButton to delete the selected layer
        self.delete_layer_button = QtWidgets.QPushButton('Delete Layer')
        self.delete_layer_button.clicked.connect(self.deleteSelectedLayer)
        self.layer_settings_layout.addWidget(self.delete_layer_button)

        # Add the layer settings widget to the right layout
        right_layout.addWidget(self.layer_settings_widget)

        # Add the right widget to the right_layout
        right_widget.setLayout(right_layout)

        # Add widgets to the main layout
        layout.addWidget(left_menu_widget)
        layout.addWidget(canvas_and_layers_widget)
        layout.addWidget(right_widget)

        # Load models and background color
        self.loadModelsAndBackgroundColor()

    def saveModelsAndBackgroundColor(self):
        # Save models and background color to a JSON file
        data = {'models': self.models_data, 'background_color': self.background_color}
        with open('models.json', 'w') as file:
            json.dump(data, file, indent=4)

    def loadModelsAndBackgroundColor(self):
        # Load models and background color from a JSON file
        if os.path.isfile('models.json'):
            with open('models.json', 'r') as file:
                data = json.load(file)
                self.models_data = data.get('models', [])
                self.background_color = data.get('background_color', (0, 255, 0))
        else:
            # If the file doesn't exist, create an empty model
            self.models_data = [{'name': 'Model 1', 'layers': []}]

        self.populateModelList()
        self.setCanvasBackgroundColor()

    def populateModelList(self):
        # Populate the model list widget
        self.model_list.clear()
        for model in self.models_data:
            self.model_list.addItem(model['name'])

        # Hide layer-related controls if no model is selected
        selected_item = self.model_list.currentItem()
        if not selected_item:
            self.layer_list.clear()
            self.layer_info_label.clear()
            self.layer_thumbnail_label.clear()
            self.layer_opacity_slider.setEnabled(False)
            self.layer_x_slider.setEnabled(False)
            self.layer_y_slider.setEnabled(False)
            self.layer_z_spinbox.setEnabled(False)
            self.delete_layer_button.setEnabled(False)
            return

        # If a model is selected, show the layers and their settings
        model_index = self.model_list.row(selected_item)
        model = self.models_data[model_index]
        self.updateLayerList(model)
        self.changeLayer()

    def updateLayerList(self, model):
        # Update the layer list widget with layers and their names
        self.layer_list.clear()
        for layer in model['layers']:
            self.layer_list.addItem(layer['name'])

    def changeModel(self):
        # Handle changing the selected model
        selected_item = self.model_list.currentItem()
        if selected_item:
            model_index = self.model_list.row(selected_item)
            model = self.models_data[model_index]
            self.updateLayerList(model)
            self.changeLayer()
        else:
            self.layer_list.clear()
            self.layer_info_label.clear()
            self.layer_thumbnail_label.clear()
            self.layer_opacity_slider.setEnabled(False)
            self.layer_x_slider.setEnabled(False)
            self.layer_y_slider.setEnabled(False)
            self.layer_z_spinbox.setEnabled(False)
            self.delete_layer_button.setEnabled(False)

    def changeLayer(self):
        # Handle changing the selected layer
        selected_item = self.layer_list.currentItem()
        if selected_item:
            model_index = self.model_list.row(self.model_list.currentItem())
            model = self.models_data[model_index]
            layer_index = self.layer_list.row(selected_item)
            layer = model['layers'][layer_index]

            # Update layer information
            self.layer_info_label.setText(f"Name: {layer['name']}\n"
                                          f"Opacity: {layer['opacity']}\n"
                                          f"Position (X, Y, Z): {layer['x']}, {layer['y']}, {layer['z']}")

            # Load and display the layer thumbnail (you need to implement this)
            # For now, let's assume the thumbnail path is stored in layer['thumbnail']
            thumbnail_path = layer.get('thumbnail', '')
            self.loadAndDisplayThumbnail(thumbnail_path)

            # Enable layer controls
            self.layer_opacity_slider.setEnabled(True)
            self.layer_x_slider.setEnabled(True)
            self.layer_y_slider.setEnabled(True)
            self.layer_z_spinbox.setEnabled(True)
            self.delete_layer_button.setEnabled(True)
        else:
            self.layer_info_label.clear()
            self.layer_thumbnail_label.clear()
            self.layer_opacity_slider.setEnabled(False)
            self.layer_x_slider.setEnabled(False)
            self.layer_y_slider.setEnabled(False)
            self.layer_z_spinbox.setEnabled(False)
            self.delete_layer_button.setEnabled(False)

    def loadAndDisplayThumbnail(self, thumbnail_path):
        # Load and display the layer thumbnail
        if os.path.isfile(thumbnail_path):
            thumbnail = QtGui.QPixmap(thumbnail_path)
            self.layer_thumbnail_label.setPixmap(thumbnail.scaled(100, 100, QtCore.Qt.KeepAspectRatio))
        else:
            self.layer_thumbnail_label.clear()

    def addEmptyModelOrClone(self):
        # Prompt the user for a name when adding an empty model or cloning
        selected_item = self.model_list.currentItem()
        new_model_name, ok = QtWidgets.QInputDialog.getText(self, 'Enter Model Name', 'Model Name:')
        if ok:
            if selected_item:
                model_index = self.model_list.row(selected_item)
                selected_model = self.models_data[model_index].copy()
                selected_model['name'] = new_model_name
                self.models_data.append(selected_model)
            else:
                self.models_data.append({'name': new_model_name, 'layers': []})

            self.populateModelList()
            self.saveModelsAndBackgroundColor()

    def deleteSelectedModel(self):
        # Delete the selected model
        selected_item = self.model_list.currentItem()
        if selected_item:
            model_index = self.model_list.row(selected_item)
            del self.models_data[model_index]
            self.populateModelList()
            self.saveModelsAndBackgroundColor()
            self.changeModel()

    def setCanvasBackgroundColor(self):
        color_index = self.bg_color_combo.currentIndex()
        if color_index == 0:  # Green (Default)
            self.central_widget_.setStyleSheet("background-color: rgba(0, 255, 0, 255);")  # Set green background
            self.background_color = (0, 255, 0)
        elif color_index == 1:  # Cyan
            self.central_widget_.setStyleSheet("background-color: rgba(0, 255, 255, 255);")
            self.background_color = (0, 255, 255)
        elif color_index == 2:  # Magenta
            self.central_widget_.setStyleSheet("background-color: rgba(255, 0, 255, 255);")
            self.background_color = (255, 0, 255)
        elif color_index == 3:  # Transparent
            self.central_widget_.setStyleSheet("background:transparent;")
            self.background_color = (0, 0, 0, 0)

        self.saveModelsAndBackgroundColor()

    def renameModel(self):
        # Rename the selected model
        selected_item = self.model_list.currentItem()
        if selected_item:
            model_index = self.model_list.row(selected_item)
            current_name = self.models_data[model_index]['name']
            new_name, ok = QtWidgets.QInputDialog.getText(self, 'Rename Model', 'New Model Name:', text=current_name)
            if ok:
                self.models_data[model_index]['name'] = new_name
                self.populateModelList()
                self.saveModelsAndBackgroundColor()

    def renameLayer(self):
        # Rename the selected layer
        selected_item = self.layer_list.currentItem()
        if selected_item:
            model_index = self.model_list.row(self.model_list.currentItem())
            model = self.models_data[model_index]
            layer_index = self.layer_list.row(selected_item)
            current_name = model['layers'][layer_index]['name']
            new_name, ok = QtWidgets.QInputDialog.getText(self, 'Rename Layer', 'New Layer Name:', text=current_name)
            if ok:
                model['layers'][layer_index]['name'] = new_name
                self.updateLayerList(model)
                self.saveModelsAndBackgroundColor()

    def updateLayerOpacity(self):
        # Update the opacity of the selected layer
        selected_item = self.layer_list.currentItem()
        if selected_item:
            model_index = self.model_list.row(self.model_list.currentItem())
            model = self.models_data[model_index]
            layer_index = self.layer_list.row(selected_item)
            opacity = self.layer_opacity_slider.value() / 100.0
            model['layers'][layer_index]['opacity'] = opacity
            self.saveModelsAndBackgroundColor()
            self.changeLayer()

    def updateLayerPositionX(self):
        # Update the X position of the selected layer
        selected_item = self.layer_list.currentItem()
        if selected_item:
            model_index = self.model_list.row(self.model_list.currentItem())
            model = self.models_data[model_index]
            layer_index = self.layer_list.row(selected_item)
            x_position = self.layer_x_slider.value()
            model['layers'][layer_index]['x'] = x_position
            self.saveModelsAndBackgroundColor()
            self.changeLayer()

    def updateLayerPositionY(self):
        # Update the Y position of the selected layer
        selected_item = self.layer_list.currentItem()
        if selected_item:
            model_index = self.model_list.row(self.model_list.currentItem())
            model = self.models_data[model_index]
            layer_index = self.layer_list.row(selected_item)
            y_position = self.layer_y_slider.value()
            model['layers'][layer_index]['y'] = y_position
            self.saveModelsAndBackgroundColor()
            self.changeLayer()

    def updateLayerZ(self):
        # Update the Z position of the selected layer
        selected_item = self.layer_list.currentItem()
        if selected_item:
            model_index = self.model_list.row(self.model_list.currentItem())
            model = self.models_data[model_index]
            layer_index = self.layer_list.row(selected_item)
            z_position = self.layer_z_spinbox.value()
            model['layers'][layer_index]['z'] = z_position
            self.saveModelsAndBackgroundColor()
            self.changeLayer()

    def deleteSelectedLayer(self):
        # Delete the selected layer
        selected_model_item = self.model_list.currentItem()
        selected_layer_item = self.layer_list.currentItem()

        if selected_model_item and selected_layer_item:
            model_index = self.model_list.row(selected_model_item)
            model = self.models_data[model_index]
            layer_index = self.layer_list.row(selected_layer_item)
            del model['layers'][layer_index]
            self.saveModelsAndBackgroundColor()
            self.changeModel()
            self.changeLayer()

    def addPicture(self):
        # Open a file dialog to select an image
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.ReadOnly
        options &= ~QtWidgets.QFileDialog.ShowDirsOnly  # Disable the "KDE-like" file dialog
        file_info, _ = QtWidgets.QFileDialog.getOpenFileUrl(self, "Open Image", QtCore.QUrl(),
                                                            "Images (*.png *.gif);;All Files (*)", options=options)

        if file_info.isValid():
            file_url = file_info.toLocalFile()

            if file_url:
                # Get the selected model
                selected_item = self.model_list.currentItem()
                if selected_item:
                    model_index = self.model_list.row(selected_item)
                    model = self.models_data[model_index]
                    # Create a new layer with default settings
                    new_layer = {
                        'name': 'Layer {}'.format(len(model['layers']) + 1),
                        'image_path': file_url,
                        'x': 0,
                        'y': 0,
                        'z': len(model['layers']),  # Incremental Z-axis
                        'opacity': 1.0
                    }
                    model['layers'].append(new_layer)
                    self.saveModelsAndBackgroundColor()
                    self.updateLayerList(model)
                    self.changeLayer()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    viewer = LayeredImageViewer()
    viewer.show()
    sys.exit(app.exec_())
