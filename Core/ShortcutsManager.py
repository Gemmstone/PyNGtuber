from PyQt6.QtCore import QThread, pyqtSignal
from pynput.keyboard import Listener
import mido


class MidiListener(QThread):
    update_shortcuts_signal = pyqtSignal(object)
    new_shortcuts_signal = pyqtSignal(object)

    def __init__(self, commands):
        super().__init__()
        self.commands = commands
        self.ignore_commands = False

    def run(self):
        with mido.open_input() as midi_port:
            for message in midi_port:
                if self.ignore_commands:
                    self.new_shortcuts_signal.emit(message)
                elif message.type == 'note_on':
                    if message in self.commands:
                        self.update_shortcuts_signal.emit(message)

    def request_new_signal(self):
        self.ignore_commands = True

    def resume_normal_operation(self):
        self.ignore_commands = False


class KeyboardListener(QThread):
    update_shortcuts_signal = pyqtSignal(list)
    new_shortcuts_signal = pyqtSignal(list)
    modifier_keys = set()  # Store the currently pressed keys

    def __init__(self, commands):
        super().__init__()
        self.commands = commands
        self.ignore_commands = False

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
                if self.ignore_commands:
                    self.update_shortcuts_signal.emit(shortcut)
                else:
                    if shortcut in self.commands:
                        self.update_shortcuts_signal.emit(shortcut)
                        self.modifier_keys = set()
        else:
            self.modifier_keys.discard(key)

    def request_new_signal(self):
        self.ignore_commands = True

    def resume_normal_operation(self):
        self.ignore_commands = False