from PyQt6.QtCore import QThread, pyqtSignal
from pynput.keyboard import Listener
import mido


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
            self.modifier_keys.discard(key)

