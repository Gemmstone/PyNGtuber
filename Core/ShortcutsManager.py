from PyQt6.QtCore import QThread, pyqtSignal
from pynput.keyboard import Listener
import mido
import os


class MidiListener(QThread):
    update_shortcuts_signal = pyqtSignal(dict)
    new_shortcuts_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.commands = {}
        self.ignore_commands = False
        self.warning = True

    def run(self):
        if os.name != 'nt':
            while True:
                with mido.open_input() as midi_port:
                    for message in midi_port:
                        if self.ignore_commands:
                            self.new_shortcuts_signal.emit({"command": message.dict(), "type": "Midi"})
                        elif message.type == 'note_on':
                            for command in self.commands:
                                if message == command["command"]:
                                    self.update_shortcuts_signal.emit(command)

    def update_shortcuts(self, commands):
        self.commands = commands

    def request_new_signal(self):
        self.ignore_commands = True

    def resume_normal_operation(self):
        self.ignore_commands = False


class KeyboardListener(QThread):
    update_shortcuts_signal = pyqtSignal(dict)
    new_shortcuts_signal = pyqtSignal(dict)
    modifier_keys = set()

    def __init__(self):
        super().__init__()
        self.commands = {}
        self.ignore_commands = False

    def run(self):
        with Listener(on_press=self.on_key_press, on_release=self.on_key_release) as listener:
            listener.join()

    def update_shortcuts(self, commands):
        self.commands = commands

    def on_key_press(self, key):
        if not hasattr(key, 'char'):
            self.modifier_keys.add(key)

    def on_key_release(self, key):
        if hasattr(key, 'char'):
            shortcut = tuple(self.modifier_keys) + (key,)
            if len(shortcut) > 1:
                if self.ignore_commands:
                    self.new_shortcuts_signal.emit(
                        {"command": [str(i).replace("'", "") for i in shortcut], "type": "Keyboard"}
                    )
                else:
                    for command in self.commands:
                        if [str(i).replace("'", "") for i in shortcut] == command["command"]:
                            self.update_shortcuts_signal.emit(command)
                    self.modifier_keys = set()
        else:
            self.modifier_keys.discard(key)

    def request_new_signal(self):
        self.ignore_commands = True

    def resume_normal_operation(self):
        self.ignore_commands = False