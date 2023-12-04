import json
# Define the folder you want to update
"""folder_to_update = "right eye"
new_posZ_value = "blinking_open"  # Set the new posZ value here

# Load the JSON data from your file
with open('Data/parameters.json', 'r') as json_file:
    data = json.load(json_file)

# Construct the target folder path
target_folder_path = f"Assets/{folder_to_update}/"

# Iterate through the JSON and update posZ for items within the target folder
for key, value in data.items():
    if target_folder_path in key:
        value['blinking'] = new_posZ_value

# Save the updated JSON back to the file
with open('Data/parameters.json', 'w') as json_file:
    json.dump(data, json_file, indent=4)

print(f"posZ values updated successfully for items within /Assets/{folder_to_update}/ folder.")
"""

# Read the JSON file
with open('Data/parameters.json', 'r') as file:
    data = json.load(file)

for key in data:
    if data[key]["hotkeys"]:
        for i, hotkey in enumerate(data[key]["hotkeys"]):
            if "mode" not in hotkey:
                data[key]["hotkeys"][i]["mode"] = "toggle"

# Save the modified data back to the JSON file
with open('Data/parameters.json', 'w') as file:
    json.dump(data, file, indent=4)

print("Keys have been modified and saved to parameters.json.")
"""
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLineEdit, QComboBox
from PyQt6.QtCore import pyqtSignal, QThread, QTimer
from pynput.keyboard import Listener, Key
from time import sleep
import mido
import sys

# A list to store your initial shortcuts
shortcuts = [
    {"type": "keyboard", "value": (Key.ctrl, "1")},
    {"type": "midi", "value": 60},
    {"type": "keyboard", "value": (Key.ctrl, "2")},
    {"type": "midi", "value": 72},
    # Add more initial shortcuts here
]


class MidiListener(QThread):
    update_shortcuts_signal = pyqtSignal(object)

    def run(self):
        with mido.open_input() as midi_port:
            for message in midi_port:
                if message.type == 'note_on':
                    self.update_shortcuts_signal.emit(message)


class KeyboardListener(QThread):
    update_shortcuts_signal = pyqtSignal(list)
    modifier_keys = set()  # Store the currently pressed keys

    def run(self):
        with Listener(on_press=self.on_key_press, on_release=self.on_key_release) as listener:
            listener.join()

    def on_key_press(self, key):
        # Store the currently pressed keys, excluding modifiers
        if not hasattr(key, 'char'):
            self.modifier_keys.add(key)

    def on_key_release(self, key):
        if hasattr(key, 'char'):
            shortcut = tuple(self.modifier_keys) + (key,)
            if len(shortcut) > 1:
                self.update_shortcuts_signal.emit(shortcut)
                self.modifier_keys = set()
        else:
            sleep(1)
            self.modifier_keys.discard(key)



# Main application window
class ShortcutManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.midi_listener = MidiListener()
        self.midi_listener.update_shortcuts_signal.connect(self.print_received)

        # Create the keyboard listener thread
        self.keyboard_listener = KeyboardListener()
        self.keyboard_listener.update_shortcuts_signal.connect(self.print_received)

        # Start the threads
        self.midi_listener.start()
        self.keyboard_listener.start()

    def print_received(self, shortcuts):
        print(f"Received: {shortcuts}")

    def init_ui(self):
        self.setWindowTitle("Shortcut Manager")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.shortcut_type_combo = QComboBox()
        self.shortcut_type_combo.addItems(["keyboard", "midi"])
        self.layout.addWidget(self.shortcut_type_combo)

        self.shortcut_value_input = QLineEdit()
        self.layout.addWidget(self.shortcut_value_input)

        self.register_button = QPushButton("Register Shortcut")
        self.register_button.clicked.connect(self.register_shortcut)
        self.layout.addWidget(self.register_button)

        self.update_button = QPushButton("Update Shortcuts")
        self.update_button.clicked.connect(self.update_shortcuts)
        self.layout.addWidget(self.update_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        self.layout.addWidget(self.exit_button)

    def register_shortcut(self):
        shortcut_type = self.shortcut_type_combo.currentText()
        shortcut_value = self.shortcut_value_input.text()
        new_shortcut = {"type": shortcut_type, "value": shortcut_value}
        shortcuts.append(new_shortcut)

    def update_shortcuts(self, new_shortcuts):
        global shortcuts
        shortcuts = new_shortcuts

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ShortcutManagerApp()
    window.show()
    sys.exit(app.exec())
"""