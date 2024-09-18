from Core.ShortcutsManager import (
    MidiListener, KeyboardListener, TwitchAPI, ShortcutsDialog,
    MouseTracker, WebSocket, HTTPServerThread
)
from PyQt6.QtGui import QIcon, QSyntaxHighlighter, QTextCharFormat, QColor, QImage, QPixmap
from PyQt6.QtCore import QCoreApplication, QEasingCurve, QThreadPool, pyqtSlot
from Core.imageGallery import ImageGallery, ExpressionSelector, ModelGallery
from Core.Viewer import LayeredImageViewer, Worker
from Core.audioManager import MicrophoneVolumeWidget
from PIL import Image, ImageSequence, ImageOps
from Core.Settings import SettingsToolBox
from PyQt6 import QtWidgets, uic, QtCore
from shutil import copy as copy_file
from collections import Counter
from pathlib import Path
import subprocess
import webbrowser
import requests
import zipfile
import psutil
import shutil
import json
import copy
import mido
import sys
import os
import re

current_version = "v1.10.2"
repo_owner = "Gemmstone"
itch_owner = "gemmstone"
itch_page = "pyngtuber"
repo_name = "PyNGtuber"

directories = ["Data", "Models", "Assets", "Viewer"]
directories_skip = ["Models", "Assets"]
overwrite_files = ["script.js", "animations.js", "viewer.html"]

os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '4864'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--no-sandbox'
os.environ["QT_SCALE_FACTOR"] = "1.0"


if os.name == 'nt':
    from ctypes import windll
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        f'gemmstone.vtubing.pyngtuber.{current_version.replace(".", "_")}'
    )


def compare_versions(current_version, latest_version):
    current_version_parts = list(map(int, re.findall(r'\d+', current_version)))
    latest_version_parts = list(map(int, re.findall(r'\d+', latest_version)))

    for i in range(min(len(current_version_parts), len(latest_version_parts))):
        if current_version_parts[i] < latest_version_parts[i]:
            return False  # Outdated
        elif current_version_parts[i] > latest_version_parts[i]:
            return True   # Ahead of latest version

    if len(current_version_parts) < len(latest_version_parts):
        return False  # Outdated
    elif len(current_version_parts) > len(latest_version_parts):
        return True   # Ahead of latest version
    else:
        return True   # Up to date


def is_path(string):
    # Check if the string is an absolute path
    if os.path.isabs(string):
        return True
    # Check if the string has an extension
    _, extension = os.path.splitext(string)
    if extension:
        return True
    # Check if the string contains path separators
    if os.path.sep in string:
        return True
    return False


def update_nested_dict(dest_data, source_data):
    for key, value in source_data.items():
        pass
        if isinstance(value, dict):
            if is_path(os.path.normpath(key)):
                if os.path.normpath(key) not in dest_data:
                    dest_data[os.path.normpath(key)] = value
                else:
                    update_nested_dict(dest_data[os.path.normpath(key)], value)
            else:
                if key not in dest_data:
                    dest_data[key] = value
                else:
                    update_nested_dict(dest_data[key], value)
        else:
            if is_path(os.path.normpath(key)):
                if os.path.normpath(key) not in dest_data:
                    dest_data[os.path.normpath(key)] = value
            else:
                if key not in dest_data:
                    dest_data[key] = value

    return dest_data


def update_json_file(source_path, dest_path):
    with open(source_path, 'r') as source_file:
        source_data = json.load(source_file)
    if isinstance(source_data, list):
        return

    if os.path.exists(dest_path):
        try:
            with open(dest_path, 'r') as dest_file:
                dest_data = json.load(dest_file)

            if isinstance(dest_data, list):
                with open(dest_path, 'w', encoding='utf-8') as dest_file:
                    json.dump(source_data, dest_file, indent=4, ensure_ascii=False)
            else:
                pass
                # dest_data = update_nested_dict(dest_data, source_data)

                # with open(dest_path, 'w') as dest_file:
                #     json.dump(dest_data, dest_file, indent=4, ensure_ascii=False)
        except BaseException:
            shutil.copyfile(source_path, dest_path)
    else:
        shutil.copyfile(source_path, dest_path)


def update_directory(source_dir, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for filename in os.listdir(source_dir):
        if filename == "script.js":
            pass
        source_path = os.path.join(source_dir, filename)
        dest_path = os.path.join(dest_dir, filename)

        if os.path.isdir(source_path):
            update_directory(source_path, dest_path)
        elif filename.endswith('.json'):
            update_json_file(source_path, dest_path)
        elif not os.path.exists(dest_path) or filename in overwrite_files:
            shutil.copyfile(source_path, dest_path)


exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
res_dir = exe_dir
prod = True if not os.path.isfile(os.path.join(exe_dir, ".gitignore")) else False

os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '4864' if prod else '4854'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--no-sandbox'

if prod:
    process = psutil.Process(os.getpid())
    if os.name == 'posix':
        if sys.platform == 'darwin':
            res_dir = os.path.expanduser("~/Library/Application Support/PyNGtuber")
        else:
            res_dir = os.path.expanduser("~/.config/PyNGtuber")
    elif os.name == 'nt':
        process.nice(psutil.REALTIME_PRIORITY_CLASS)
        res_dir = os.path.join(os.getenv("APPDATA"), "PyNGtuber")

    for directory in directories:
        src_path = os.path.join(exe_dir, directory)
        dest_path = os.path.join(res_dir, directory)

        if not os.path.exists(dest_path):

            shutil.copytree(src_path, dest_path)
        elif directory not in directories_skip:
            update_directory(src_path, dest_path)


class twitchKeysDialog(QtWidgets.QWidget):
    new_keys = QtCore.pyqtSignal(dict)

    def __init__(self, APP_ID, APP_SECRET, APP_USER, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(exe_dir, f"UI", "auth_twitch.ui"), self)

        self.APP_ID = APP_ID
        self.APP_SECRET = APP_SECRET
        self.APP_USER = APP_USER

        self.client.setText(self.APP_ID)
        self.secret.setText(self.APP_SECRET)
        self.user.setText(self.APP_USER)

        self.saveKeysBtn.clicked.connect(self.save)

    def save(self):
        self.APP_ID = self.client.text() if self.client.text() else None
        self.APP_SECRET = self.secret.text() if self.secret.text() else None
        self.APP_USER = self.user.text() if self.user.text() else None

        self.new_keys.emit({
            "APP_ID": self.APP_ID,
            "APP_SECRET": self.APP_SECRET,
            "APP_USER": self.APP_USER
        })


class UpdateDialog(QtWidgets.QDialog):
    def __init__(self, latest_version, data, parent=None):
        super().__init__(parent)
        uic.loadUi(os.path.join(exe_dir, f"UI", "update.ui"), self)
        self.setWindowTitle("Update Available")

        self.data = data

        for key, item in self.data.items():
            print(key, ":", item)

        self.changelog.setPlainText(self.format_changelog(self.data["body"].split("Changelog")[-1].strip()))

        self.title.setText(self.data["name"])
        self.label_2.setText(f"A new version of {repo_name} is available!")
        self.label_3.setText(f" {latest_version} ")
        self.label_5.setText(f"{self.data['published_at'].split('T')[0].replace('-', '/')}")

        self.update.hide()
        self.update.clicked.connect(self.download)
        self.gotopage.clicked.connect(self.go_to_page)
        self.skip.clicked.connect(self.ignore)

    def format_changelog(self, text):
        lines = text.split('\n')
        formatted_text = ''
        for line in lines:
            if line.strip():
                if line.strip().startswith('*'):
                    formatted_text += '• ' + line[1:].strip() + '\n'
                elif line.strip().startswith('-'):
                    formatted_text += '   • ' + line[4:].strip() + '\n'
                elif line.strip().startswith('+'):
                    formatted_text += '      • ' + line[4:].strip() + '\n'
                else:
                    formatted_text += line.strip() + '\n'
        return formatted_text.strip()

    def download(self):
        if os.path.isfile(os.path.join(exe_dir, 'main.exe')):
            self.download_app('Windows')
        elif os.path.isfile(os.path.join(exe_dir, 'main.py')):
            self.download_app('Python')
        else:
            self.download_app('Linux')

    def download_app(self, platform_name):
        download_url = None
        if platform_name == "Python":
            download_url = f"https://github.com/{repo_owner}/{repo_name}/archive/refs/tags/{self.data['tag_name']}.zip"
        else:
            for asset in self.data['assets']:
                if platform_name in asset['name']:
                    download_url = asset['browser_download_url']

        if download_url:
            download_dialog = QtWidgets.QProgressDialog("Downloading update. Please wait...", "", 0, 0, self)
            download_dialog.setWindowTitle("Downloading...")
            download_dialog.setCancelButton(None)
            download_dialog.setModal(True)
            download_dialog.setValue(0)
            download_dialog.show()
            with requests.get(download_url, stream=True) as r:
                with open(os.path.join(exe_dir, 'update.zip'), 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            download_dialog.accept()

        if os.path.isfile(os.path.join(exe_dir, 'update.zip')):
            extracting_dialog = QtWidgets.QProgressDialog("Downloading update. Please wait...", "", 0, 0, self)
            extracting_dialog.setWindowTitle("Extracting...")
            extracting_dialog.setCancelButton(None)
            extracting_dialog.setModal(True)
            extracting_dialog.setValue(0)
            extracting_dialog.show()
            extracting_dialog.setWindowTitle("Extracting...")
            with zipfile.ZipFile(os.path.join(exe_dir, 'update.zip'), 'r') as zip_ref:
                if platform_name == "Python":
                    zip_file_name = zip_ref.namelist()[0]
                    zip_ref.extractall(
                        exe_dir,
                        members=[
                            member for member in zip_ref.namelist()
                            if member.startswith(zip_file_name) and len(member) > len(zip_file_name) + 1
                        ]
                    )
                else:
                    zip_ref.extractall(exe_dir)
            extracting_dialog.accept()

            os.remove(os.path.join(exe_dir, 'update.zip'))

        self.accept()

    def go_to_page(self):
        # webbrowser.open(f"https://github.com/{repo_owner}/{repo_name}/releases/tag/{self.data['tag_name']}")
        webbrowser.open(f"https://{itch_owner}.itch.io/{itch_page}")

    def ignore(self):
        self.reject()


class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document, document_type):
        super().__init__(document)
        self.highlightingRules = []
        match document_type:
            case "htmlCode":
                # HTML tag format
                tag_format = QTextCharFormat()
                tag_format.setForeground(QColor("#0000FF"))
                tag_pattern = QtCore.QRegularExpression(r"</?[\w\s]*>")
                self.highlightingRules.append((tag_pattern, tag_format))

                # HTML attribute format
                attribute_format = QTextCharFormat()
                attribute_format.setForeground(QColor("#FF0000"))
                attribute_pattern = QtCore.QRegularExpression(r'\b\w+="[^"]*"')
                self.highlightingRules.append((attribute_pattern, attribute_format))

            case "jsCode":
                # JS keyword format
                js_keyword_format = QTextCharFormat()
                js_keyword_format.setForeground(QColor("#0000FF"))
                js_keywords = ["var", "let", "const", "function", "if", "else", "for", "while", "return"]
                for keyword in js_keywords:
                    pattern = QtCore.QRegularExpression(f"\\b{keyword}\\b")
                    self.highlightingRules.append((pattern, js_keyword_format))

                # JS string format
                string_format = QTextCharFormat()
                string_format.setForeground(QColor("#FF00FF"))
                string_patterns = [r'"[^"]*"', r"'[^']*'"]
                for pattern in string_patterns:
                    string_pattern = QtCore.QRegularExpression(pattern)
                    self.highlightingRules.append((string_pattern, string_format))

                # JS comment format
                comment_format = QTextCharFormat()
                comment_format.setForeground(QColor("#808080"))
                comment_patterns = [r'//[^\n]*', r'/\*.*\*/']
                for pattern in comment_patterns:
                    comment_pattern = QtCore.QRegularExpression(pattern)
                    self.highlightingRules.append((comment_pattern, comment_format))

            case "cssCode":
                # CSS selector format
                css_selector_format = QTextCharFormat()
                css_selector_format.setForeground(QColor("#800080"))
                css_selector_pattern = QtCore.QRegularExpression(r'\b[\w-]+\s*{')
                self.highlightingRules.append((css_selector_pattern, css_selector_format))

                # CSS property format
                css_property_format = QTextCharFormat()
                css_property_format.setForeground(QColor("#008000"))
                css_property_pattern = QtCore.QRegularExpression(r'\b[\w-]+\s*:')
                self.highlightingRules.append((css_property_pattern, css_property_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlightingRules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
        self.setCurrentBlockState(0)


class HiddenWindow(QtWidgets.QWidget):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("PyNGtuber Capture")
        # self.setWindowFlag(QtCore.Qt.WindowType.Tool)    Windows and Discord don't like this!
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnBottomHint)
        self.viewer = LayeredImageViewer(exe_dir=res_dir, hw_acceleration=settings.get("hardware acceleration", False))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.viewer)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


class FileParametersDefault:
    def __init__(self, base_path, in_memory_only=False):
        self.base_path = base_path
        self.in_memory_only = in_memory_only
        self.default_default_value = {
            "sizeX": 600,
            "sizeY": 600,
            "posX": 0,
            "posY": 0,
            "posZ": 40,
            "animation": [],
            "css": "",
            "blinking": "ignore",
            "talking": [
                "ignore"
            ],
            "hotkeys": [],
            "rotation": 0,
            "use_css": False,
            "controller": [
                "ignore"
            ],
            "originX": 0,
            "originY": 0,
            "deg": 90,
            "originXright": 0,
            "originYright": 0,
            "degRight": 90,
            "originXzoom": 0,
            "originYzoom": 0,
            "degZoom": 90,
            "originXwhammy": 0,
            "originYwhammy": 0,
            "degWhammy": 0,
            "deadzone": 0.055,
            "player": 1,
            "player2": 1,
            "buttons": 0,
            "invertAxis": 0,
            "chords": [],
            "cursorScaleX": 0.003,
            "cursorScaleY": 0.004,
            "invert_mouse_x": 0,
            "invert_mouse_y": 1,
            "track_mouse_x": 1,
            "track_mouse_y": 1,
            "cursor": False,
            "mode": "display",
            "posBothX": 0,
            "posBothY": 0,
            "rotationBoth": 0,
            "posLeftX": 0,
            "posLeftY": 0,
            "rotationLeft": 0,
            "posRightX": 0,
            "posRightY": 0,
            "rotationRight": 0,
            "posGuitarUpX": 0,
            "posGuitarUpY": 0,
            "rotationGuitarUp": 0,
            "posGuitarDownX": 0,
            "posGuitarDownY": 0,
            "rotationGuitarDown": 0,
            "animation_idle": True,
            "animation_name_idle": "None",
            "animation_name_talking": "None",
            "animation_speed_idle": 6.0,
            "animation_speed_talking": 0.5,
            "animation_direction_idle": "normal",
            "animation_direction_talking": "normal",
            "filename": "ahoge_001.png",
            "parent_folder": "ahoge",
            "thumbnail_path": "Assets/Chereverie/ahoge/thumbs/ahoge_001.png",
            "title": "ahoge_001.png",
            "move": False,
            "moveToIDLE": True,
            "moveToTALKING": True,
            "moveToSCREAMING": True,
            "idle_position_speed": 0.2,
            "idle_position_pacing": "EaseInOut",
            "sizeX_talking": 600,
            "sizeY_talking": 600,
            "posX_talking": 0,
            "posY_talking": 0,
            "rotation_talking": 0,
            "talking_position_speed": 0.2,
            "talking_position_pacing": "EaseInOut",
            "sizeX_screaming": 600,
            "sizeY_screaming": 600,
            "posX_screaming": 0,
            "posY_screaming": 0,
            "rotation_screaming": 0,
            "screaming_position_speed": 0.2,
            "screaming_position_pacing": "EaseInOut",
            "animation_name_screaming": "None",
            "animation_speed_screaming": 0.5,
            "animation_direction_screaming": "normal",
            "animation_iteration_idle": 0,
            "animation_iteration_talking": 0,
            "animation_iteration_screaming": 0,
            "animation_pacing_idle": "EaseInOut",
            "animation_pacing_talking": "EaseInOut",
            "animation_pacing_screaming": "EaseInOut",
            "shadow": False,
            "color": "#000000",
            "shadowBlur": 20,
            "shadowOpacity": 100,
            "shadowX": 0,
            "shadowY": 0,
            "filters": False,
            "hue": 0.0,
            "saturation": 100.0,
            "brightness": 100.0,
            "contrast": 100.0,
            "opacity": 100.0,
            "blur": 0.0,
            "grayscale": 0.0,
            "invert": 0.0,
            "sepia": 0.0,
            "forced_mouse_tracking": 0
        }
        self.memory_store = {}

    def _load_json(self, route):
        json_path = os.path.join(self.base_path, f"{route}.json")
        if os.path.isfile(json_path):
            with open(json_path, 'r') as file:
                return json.load(file)
        return None

    def _create_json_file(self, route, settings):
        json_path = os.path.join(self.base_path, f"{route}.json")
        try:
            with open(json_path, 'w') as file:
                json.dump(settings, file, indent=4)
        except FileNotFoundError:
            pass
        return settings

    def __getitem__(self, route):
        if self.in_memory_only:
            if route in self.memory_store:
                return self.memory_store[route]
            else:
                self.memory_store[route] = self._load_json(route)
                if self.memory_store[route] is None:
                    self._create_json_file(route, copy.deepcopy(self.default_default_value))
                    self.memory_store[route] = self._load_json(route)
                return self.memory_store[route]
        else:
            json_data = self._load_json(route)
            if json_data is None:
                self._create_json_file(route, copy.deepcopy(self.default_default_value))
                self.memory_store[route] = self._load_json(route)
            return json_data

    def __setitem__(self, route, settings):
        if self.in_memory_only:
            self.__getitem__(route)
            self.memory_store[route] = settings

    def __iter__(self):
        if self.in_memory_only:
            return iter(self.memory_store)

    def get_shortcuts(self):
        for root, dirs, files in os.walk(os.path.join(res_dir, "Assets")):
            for filename in files:
                if filename.endswith(".json"):
                    data_json_path = os.path.join(root, filename)
                    with open(data_json_path, 'r') as json_file:
                        data = json.load(json_file)
                        shortcut = data.get("hotkeys", [])

                        data_json_path = os.path.join(
                            "Assets", copy.deepcopy(data_json_path).split(f"Assets{os.path.sep}")[-1]
                        )

                        for hotkey in shortcut:
                            yield data_json_path.replace(".json", "", -1), hotkey

    def __len__(self):
        if self.in_memory_only:
            return len(self.memory_store)

    def __contains__(self, route):
        if self.in_memory_only:
            self.__getitem__(route)
            return route in self.memory_store


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.hidden_ui = False
        uic.loadUi(os.path.join(exe_dir, f"UI", "main.ui"), self)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowMinimizeButtonHint)

        # self.tabWidget_2.setTabVisible(2, False)
        self.groupBox_24.hide()
        self.groupBox_25.hide()
        self.groupBox_27.hide()


        self.settings_json_file = os.path.join(res_dir, "Data", "settings.json")
        try:
            with open(self.settings_json_file, "r") as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            pass

        assets_folder = os.path.join(res_dir, "Assets")
        self.collections = [
            entry for entry in os.listdir(assets_folder) if os.path.isdir(os.path.join(assets_folder, entry))
        ]
        for collection in self.collections:
            self.collection.addItem(collection)

        self.htmlCode_highlighter = SyntaxHighlighter(self.htmlCode.document(), "htmlCode")
        self.jsCode_highlighter = SyntaxHighlighter(self.jsCode.document(), "jsCode")
        self.cssCode_highlighter = SyntaxHighlighter(self.cssCode.document(), "cssCode")
        self.animCode_highlighter = SyntaxHighlighter(self.animCode.document(), "cssCode")

        self.general_shadow = None
        self.general_filters = None

        self.viewer = LayeredImageViewer(
            exe_dir=res_dir,
            enabled=self.settings.get("local_canvas_source_toggle", True),
            hw_acceleration=self.settings.get("hardware acceleration", False)
        )
        self.viewer.failed_to_load_images.connect(self.retry_load)
        self.viewer.loadFinishedSignal.connect(self.reboot_audio)
        self.viewer.div_count_signal.connect(self.update_div_count)
        self.viewerFrame.layout().addWidget(self.viewer)

        self.threadpool = QThreadPool()

        self.edited = None
        self.photoMode = None
        self.color = "limegreen"
        self.viewerFrame_2.setStyleSheet(f"background-color: {self.color}")

        self.setWindowTitle("PyNGTuber")

        self.label_7.setText(
            f'<a href="https://github.com/{repo_owner}/{repo_name}/releases/tag/{current_version}">{current_version}</a>'
        )

        self.color = (184, 205, 238)
        # self.file_parameters_current = {}
        self.current_files = []
        self.TwitchAPI = None
        self.current_json_file = os.path.join(res_dir, "Data", "current.json")
        self.current_model_json_file = os.path.join(res_dir, "Data", "current_model.json")
        self.current_expression_json_file = os.path.join(res_dir, "Data", "current_expression.json")
        self.apiKeys = os.path.join(res_dir, "Data", "keys.json")

        self.js_file = os.path.join(res_dir, "Viewer", "script.js")
        self.css_file = os.path.join(res_dir, "Viewer", "styles.css")
        self.anim_file = os.path.join(res_dir, "Viewer", "animations.css")
        self.html_file = os.path.join(res_dir, "Viewer", "viewer.html")

        self.js_file_default = os.path.join(exe_dir, "Viewer", "script.js")
        self.css_file_default = os.path.join(exe_dir, "Viewer", "styles.css")
        self.anim_file_default = os.path.join(exe_dir, "Viewer", "animations.js")
        self.html_file_default = os.path.join(exe_dir, "Viewer", "viewer.html")

        self.selected_animations = {
            0: {
                "animation": self.idle_animation,
                "speed": self.idle_speed,
                "direction": self.idle_animation_direction,
                "easing": self.idle_animation_easing,
                "iteration": self.idle_animation_iteration
            },
            1: {
                "animation": self.talking_animation,
                "speed": self.talking_speed,
                "direction": self.talking_animation_direction,
                "easing": self.talking_animation_easing,
                "iteration": self.talking_animation_iteration
            },
            2: {
                "animation": self.screaming_animation,
                "speed": self.screaming_speed,
                "direction": self.screaming_animation_direction,
                "easing": self.screaming_animation_easing,
                "iteration": self.screaming_animation_iteration
            }
        }

        self.keyboard_listener = KeyboardListener()
        self.keyboard_listener.shortcut.connect(self.shortcut_received)
        self.keyboard_listener.start()
        self.midi_listener = MidiListener()
        self.midi_listener.shortcut.connect(self.shortcut_received)
        self.midi_listener.start()

        self.file_parameters_default = FileParametersDefault(res_dir)
        self.file_parameters_current = FileParametersDefault(res_dir, True)

        try:
            with open(self.current_json_file, "r") as f:
                self.current_files = json.load(f)
        except FileNotFoundError:
            pass

        try:
            with open(self.current_model_json_file, "r") as f:
                self.current_model = json.load(f)
                self.last_model = copy.deepcopy(self.current_model)
        except FileNotFoundError:
            pass

        try:
            with open(self.current_expression_json_file, "r") as f:
                self.current_expression = json.load(f)
                self.last_expression = copy.deepcopy(self.current_expression)
        except FileNotFoundError:
            pass

        try:
            with open(self.apiKeys, "r") as f:
                keys = json.load(f)
                self.twitch_user = keys["twitch"].get("user", None) if keys["twitch"].get("user", "") else None
                self.twitch_api_client = keys["twitch"]["client"] if keys["twitch"]["client"] else None
                self.twitch_api_secret = keys["twitch"]["secret"] if keys["twitch"]["secret"] else None
        except FileNotFoundError:
            self.twitch_api_client = None
            self.twitch_api_secret = None
            self.twitch_user = None

        self.start_twitch_connection({
            "APP_ID": self.twitch_api_client,
            "APP_SECRET": self.twitch_api_secret
        }, True)

        self.current_files = [os.path.normpath(i) for i in self.current_files]

        try:
            with open(self.js_file, "r") as f:
                self.jsCode.setPlainText(f.read())
        except FileNotFoundError:
            pass

        try:
            with open(self.css_file, "r") as f:
                self.cssCode.setPlainText(f.read())
        except FileNotFoundError:
            pass

        try:
            with open(self.anim_file, "r") as f:
                self.animCode.setPlainText(f.read())
        except FileNotFoundError:
            pass

        self.get_shortcuts()

        self.audio = MicrophoneVolumeWidget(
            exe_dir=exe_dir,
            engine=self.settings.get('audio engine', "pyaudio"),
            noise_reduction=self.settings.get("noise_reduction", True),
            sample_rate_noise_reduction=self.settings.get("sample_rate", 44100),
        )
        self.audio.activeAudio.connect(self.audioStatus)
        self.audioFrame.layout().addWidget(self.audio)
        self.audio.load_settings(settings=self.settings)

        self.idle_animation.activated.connect(self.update_settings)
        # self.idle_animation_pacing.activated.connect(self.update_settings)
        self.idle_animation_direction.activated.connect(self.update_settings)
        self.idle_speed.valueChanged.connect(self.update_settings)
        self.idle_animation_iteration.valueChanged.connect(self.update_settings)

        self.talking_animation.activated.connect(self.update_settings)
        # self.talking_animation_pacing.activated.connect(self.update_settings)
        self.talking_animation_direction.activated.connect(self.update_settings)
        self.talking_speed.valueChanged.connect(self.update_settings)
        self.talking_animation_iteration.valueChanged.connect(self.update_settings)

        self.screaming_animation.activated.connect(self.update_settings)
        # self.screaming_animation_pacing.activated.connect(self.update_settings)
        self.screaming_animation_direction.activated.connect(self.update_settings)
        self.screaming_speed.valueChanged.connect(self.update_settings)
        self.screaming_animation_iteration.valueChanged.connect(self.update_settings)

        self.load_settings()

        if self.second_window_toggle.isChecked():
            self.hidden_window = HiddenWindow(self.settings)

        self.comboBox.currentIndexChanged.connect(self.update_settings)
        self.PNGmethod.currentIndexChanged.connect(self.update_settings)
        self.HideUI.toggled.connect(self.update_settings)
        self.windowAnimations.toggled.connect(self.update_settings)
        self.flipCanvasToggleH.toggled.connect(self.flipCanvas)
        self.flipCanvasToggleV.toggled.connect(self.flipCanvas)

        self.track_mouse_x.toggled.connect(self.toggle_track_mouse_x)
        self.track_mouse_y.toggled.connect(self.toggle_track_mouse_y)

        self.cameraSelector.valueChanged.connect(self.cameraSelector_update)
        self.alphaSelector.valueChanged.connect(self.alphaSelector_update)

        self.privacy_mode.toggled.connect(self.privacy_mode_update)
        self.privacy_mode.toggled.connect(self.update_settings)

        self.cameraSelector.valueChanged.connect(self.update_settings)
        self.alphaSelector.valueChanged.connect(self.update_settings)
        self.speed_movement.valueChanged.connect(self.update_settings)
        self.scale_x.valueChanged.connect(self.update_settings)
        self.opacity_speed.valueChanged.connect(self.update_settings)
        self.scale_camera_x.valueChanged.connect(self.update_settings)
        self.scale_y.valueChanged.connect(self.update_settings)
        self.scale_camera_y.valueChanged.connect(self.update_settings)

        self.tracking_position_pacing.currentIndexChanged.connect(self.update_settings)

        self.move_idle_random.toggled.connect(self.update_settings)
        self.move_talking_random.toggled.connect(self.update_settings)
        self.move_screaming_random.toggled.connect(self.update_settings)

        self.scale_random_x.valueChanged.connect(self.update_settings)
        self.scale_random_y.valueChanged.connect(self.update_settings)

        self.noise_reduction.toggled.connect(self.change_noise_reduction)
        self.sample_rate.valueChanged.connect(self.change_sample_rate)

        self.local_obs_source_toggle.toggled.connect(self.hide_local_obs_source_toggle)
        self.remote_obs_source_toggle.toggled.connect(self.hide_remote_obs_source_toggle)

        self.exportToPNG.clicked.connect(self.save_canvas_image)

        self.webSocketToggle.toggled.connect(self.hide_webSocket)
        self.auto_flip.toggled.connect(self.auto_flip_hide)

        self.webSocketToggle.toggled.connect(self.update_settings)
        self.webSocketPort.valueChanged.connect(self.update_settings)

        self.auto_flip.toggled.connect(self.update_settings)
        self.flip_camera_x.valueChanged.connect(self.update_settings)

        self.track_mouse_x.toggled.connect(self.update_settings)
        self.track_mouse_y.toggled.connect(self.update_settings)
        self.invert_mouse_x.toggled.connect(self.update_settings)
        self.invert_mouse_y.toggled.connect(self.update_settings)

        self.ImageGallery = ImageGallery(
            self.current_files, res_dir=res_dir, exe_dir=exe_dir,
            collection=self.collection.currentText(),
            memory=self.file_parameters_current
        )
        self.ImageGallery.selectionChanged.connect(self.update_viewer)
        self.ImageGallery.currentChanged.connect(self.change_settings_gallery)
        self.scrollArea.setWidget(self.ImageGallery)

        self.comboBox.currentIndexChanged.connect(self.setBGColor)

        self.SettingsGallery = SettingsToolBox(
            exe_dir=exe_dir, res_dir=res_dir, viewer=self.viewer, anim_file=self.anim_file
        )
        self.SettingsGallery.settings_changed.connect(self.saveSettings)
        self.SettingsGallery.settings_changed_list.connect(self.saveSettings_list)
        self.SettingsGallery.currentChanged.connect(self.being_edited)
        self.SettingsGallery.shortcut.connect(self.dialog_shortcut)
        self.SettingsGallery.delete_shortcut.connect(self.delete_shortcut)
        self.scrollArea_2.setWidget(self.SettingsGallery)

        self.animations_list = []
        self.update_animations(self.settings["animations"])

        self.expressionSelector = ExpressionSelector("Assets")
        self.frame_46.layout().addWidget(self.expressionSelector)

        self.savedAvatars = [folder for folder in os.listdir(os.path.join(res_dir, "Models", "Avatars")) if "." not in folder]
        self.modelGallery = ModelGallery(models_list=self.savedAvatars, models_type="Avatars", exe_dir=exe_dir, res_dir=res_dir)
        self.modelGallery.saving.connect(self.save_avatar)
        self.modelGallery.selected.connect(self.load_model)
        self.modelGallery.shortcut.connect(self.dialog_shortcut)
        self.frameModels.layout().addWidget(self.modelGallery)

        self.savedExpressions = [folder for folder in os.listdir(os.path.join(res_dir, "Models", "Expressions")) if "." not in folder]
        self.expressionGallery = ModelGallery(models_list=self.savedExpressions, models_type="Expressions", exe_dir=exe_dir, res_dir=res_dir)
        self.expressionGallery.saving.connect(self.save_expression)
        self.expressionGallery.selected.connect(self.load_model)
        self.expressionGallery.shortcut.connect(self.dialog_shortcut)
        self.frameExpressions.layout().addWidget(self.expressionGallery)

        self.twitch_dialog = twitchKeysDialog(
            APP_ID=self.twitch_api_client,
            APP_SECRET=self.twitch_api_secret,
            APP_USER=self.twitch_user
        )
        self.twitch_dialog.new_keys.connect(self.start_twitch_connection)
        self.twitch_integration.layout().addWidget(self.twitch_dialog)

        self.setBGColor()
        self.showUI()

        self.PNG.clicked.connect(lambda: self.export_png())

        self.saveAvatar.clicked.connect(self.save_avatar)
        self.saveExpression.clicked.connect(self.save_expression)

        self.color_selector.clicked.connect(self.showColorDialog)

        self.createCategory.clicked.connect(self.CreateCategory)
        self.createCollection.clicked.connect(self.CreateCollection)
        self.openFolder.clicked.connect(self.OpenAssetsFolder)
        self.clear.clicked.connect(self.clearSelection)

        self.tabWidget_2.currentChanged.connect(self.changePage)

        self.editorButton.clicked.connect(self.toggle_editor)
        self.closeEditor.clicked.connect(self.toggle_editor)

        self.saveViewerBtn.clicked.connect(self.update_viewer_files)

        self.restoreDefaultsBTN.clicked.connect(self.restore_defaults)

        self.audio_engine.currentIndexChanged.connect(self.change_audio_engine)
        self.collection.currentIndexChanged.connect(self.change_collection)

        self.reference_volume.valueChanged.connect(self.change_max_reference_volume)

        self.generalScale.valueChanged.connect(self.on_zoom_delta_changed)
        self.resetZoom.clicked.connect(lambda: self.generalScale.setValue(100))

        self.shadow_toggle.toggled.connect(self.hide_shadow)
        self.shadowBlur.valueChanged.connect(self.update_shadow)
        self.shadowX.valueChanged.connect(self.update_shadow)
        self.shadowY.valueChanged.connect(self.update_shadow)

        self.filters_toggle.toggled.connect(self.hide_filters)
        self.hue.valueChanged.connect(self.update_filters)
        self.saturation.valueChanged.connect(self.update_filters)
        self.brightness.valueChanged.connect(self.update_filters)
        self.contrast.valueChanged.connect(self.update_filters)
        self.opacity.valueChanged.connect(self.update_filters)
        self.blur.valueChanged.connect(self.update_filters)
        self.grayscale.valueChanged.connect(self.update_filters)
        self.invert.valueChanged.connect(self.update_filters)
        self.sepia.valueChanged.connect(self.update_filters)

        self.photoAvatarBody.toggled.connect(self.being_edited)
        self.photoAvatarFace.toggled.connect(self.being_edited)
        self.photoAvatarBody.toggled.connect(self.show_model_photo_mode)
        self.photoAvatarFace.toggled.connect(self.show_model_photo_mode)
        self.photoEyesOpen.toggled.connect(self.being_edited)
        self.photoMouthClosed.toggled.connect(self.being_edited)
        self.photoMouthOpen.toggled.connect(self.being_edited)
        self.photoMouthScreaming.toggled.connect(self.being_edited)
        self.photoFiltersEnabled.toggled.connect(self.being_edited)
        self.photoFiltersDisabled.toggled.connect(self.being_edited)
        self.photoShadowsEnabled.toggled.connect(self.being_edited)
        self.photoShadowsDisabled.toggled.connect(self.being_edited)
        self.photoCSSEnabled.toggled.connect(self.being_edited)
        self.photoCSSDisabled.toggled.connect(self.being_edited)
        self.photoAnimationsEnabled.toggled.connect(self.being_edited)
        self.photoAnimationsDisabled.toggled.connect(self.being_edited)

        self.mouseTrackingToggle.toggled.connect(self.mouse_tracking_changed)
        self.randomTrackingToggle.toggled.connect(self.mouse_tracking_changed)
        self.faceTrackingToggle.toggled.connect(self.mouse_tracking_changed)
        self.disableTrackingToggle.toggled.connect(self.mouse_tracking_changed)
        self.transparency.toggled.connect(self.being_edited)
        self.performance.toggled.connect(lambda: self.update_viewer(self.current_files, update_gallery=True))

        self.local_canvas_source_toggle.toggled.connect(self.toggle_viewer)

        self.toggle_editor()
        self.change_audio_engine()
        self.being_edited()

        self.hide_webSocket()
        self.auto_flip_hide()
        self.change_noise_reduction()

        self.hide_local_obs_source_toggle()
        self.hide_remote_obs_source_toggle()

        self.toggle_track_mouse_x()
        self.toggle_track_mouse_y()

        self.hide_shadow()
        self.hide_filters()

        self.mouse_tracker = MouseTracker(
            camera=self.settings.get("camera", True),
            target_fps=self.alphaSelector.value(),
            privacy_mode=self.privacy_mode.isChecked()
        )
        self.mouse_tracker.frame_received.connect(self.update_camera_feed)
        self.mouse_tracker.mouse_position.connect(self.on_mouse_position_changed)

        self.forced_mouse_tracker = MouseTracker(target_fps=self.alphaSelector.value())
        self.forced_mouse_tracker.mouse_position.connect(self.on_mouse_position_forced)
        self.mouse_tracking_changed()

        self.web_socket = WebSocket(
            res_dir,
            self.webSocketPort.value() if prod else self.webSocketPort.value() + 10
        )
        self.web_socket.model_command.connect(self.load_model)
        self.web_socket.reload_images.connect(self.reload_images)
        self.web_socket.asset_command.connect(self.shortcut_received)

        if self.webSocketToggle.isChecked():
            self.web_socket.start()

        self.web_socket_obs = WebSocket(res_dir, port=4863 if prod else 4853)
        self.web_socket_obs.reload_images.connect(self.reload_images)
        if self.local_obs_source_toggle.isChecked():
            self.web_socket_obs.start()

        self.obs_address.setAccessibleName(
            f"file:///{self.html_file}?server_address={self.web_socket_obs.ip_address}:{self.web_socket_obs.port}"
        )

        self.web_socket_obs_remote = WebSocket(res_dir, False, 4861 if prod else 4851)
        self.web_socket_obs_remote.reload_images.connect(self.reload_images)

        self.html_server = HTTPServerThread(self.web_socket_obs_remote.ip_address, 4862 if prod else 4852, res_dir)
        self.html_server.server_started.connect(lambda: self.obs_address_remote.setAccessibleName(
            f"http://{self.web_socket_obs_remote.ip_address}:{self.html_server.port}/Viewer/viewer.html"
            f"?server_address={self.web_socket_obs_remote.ip_address}:{self.web_socket_obs_remote.port}"
        ))
        if self.remote_obs_source_toggle.isChecked():
            self.web_socket_obs_remote.start()
            self.html_server.start()

        self.obs_address.clicked.connect(self.copyUrl)
        self.obs_address_remote.clicked.connect(self.copyUrl)

        self.viewer.obs_websocket = self.web_socket_obs
        self.viewer.obs_websocket_remote = self.web_socket_obs_remote

        if os.path.isfile(os.path.join(exe_dir, 'main.exe')):
            self.noise_reduction.hide()
            self.faceTrackingToggle.hide()
        elif os.path.isfile(os.path.join(exe_dir, 'main.py')):
            pass
        else:
            pass

        self.update_shadow(False)
        self.update_filters(False)

        self.check_for_update()
        self.update_viewer(self.current_files, update_gallery=True)

        if hasattr(self, 'hidden_window'):
            if self.second_window_toggle.isChecked():
                self.hidden_window.show()

    def reboot_window(self):
        pass

    def update_shadow(self, update=True):
        self.general_shadow = None
        if self.shadow_toggle.isChecked():
            self.general_shadow = {
                "shadowColor": self.color_selector.text(),
                "shadowBlur": self.shadowBlur.value(),
                "shadowX": self.shadowX.value(),
                "shadowY": self.shadowY.value()
            }
        if update:
            self.update_settings()
            self.update_viewer(self.current_files)

    def update_filters(self, update=True):
        self.general_filters = None
        if self.filters_toggle.isChecked():
            self.general_filters = {
                "hue": self.hue.value(),
                "saturation": self.saturation.value(),
                "brightness": self.brightness.value(),
                "contrast": self.contrast.value(),
                "opacity": self.opacity.value(),
                "blur": self.blur.value(),
                "grayscale": self.grayscale.value(),
                "invert": self.invert.value(),
                "sepia": self.sepia.value()
            }
        if update:
            self.update_settings()
            self.update_viewer(self.current_files)

    def toggle_viewer(self):
        last = copy.deepcopy(self.viewer.enabled)
        if self.local_canvas_source_toggle.isChecked():
            self.viewer.enabled = True
            if not last:
                self.update_viewer(self.current_files)
        else:
            self.viewer.enabled = False
            if last:
                self.viewer.page().runJavaScript(f'document.body.style.zoom = "100%";')
                self.viewer.page().runJavaScript(f'addImagesToCanvas({str([])}, null)')
        self.update_settings()

    def hide_local_obs_source_toggle(self):
        if self.local_obs_source_toggle.isChecked():
            self.obs_address.show()
        else:
            self.obs_address.hide()
        self.update_settings()

    def hide_remote_obs_source_toggle(self):
        if self.remote_obs_source_toggle.isChecked():
            self.obs_address_remote.show()
            self.frame_71.show()
        else:
            self.obs_address_remote.hide()
            self.frame_71.hide()
        self.update_settings()

    def copyUrl(self):
        button = self.sender()
        text = button.text()
        QtWidgets.QApplication.clipboard().setText(button.accessibleName())
        button.setText("Copied!")
        QtCore.QTimer.singleShot(1500, lambda: button.setText(text))

    def hide_webSocket(self):
        if self.webSocketToggle.isChecked():
            self.frame_41.show()
        else:
            self.frame_41.hide()

    def auto_flip_hide(self):
        if self.auto_flip.isChecked():
            self.frame_43.show()
        else:
            self.frame_43.hide()

    @pyqtSlot(QImage)
    def update_camera_feed(self, qt_image):
        CameraFeed_width = self.CameraFeed.width()
        CameraFeed_height = self.CameraFeed.height()

        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(CameraFeed_width, CameraFeed_height, QtCore.Qt.AspectRatioMode.KeepAspectRatio)

        self.CameraFeed.setPixmap(scaled_pixmap)

    def cameraSelector_update(self, value):
        self.mouse_tracker.set_camera(value)

    def alphaSelector_update(self, value):
        self.mouse_tracker.set_framerate(value)
        self.forced_mouse_tracker.set_framerate(value)

    def privacy_mode_update(self):
        new_mode = self.privacy_mode.isChecked()
        if not new_mode:
            reply = QtWidgets.QMessageBox.question(self, 'Disable Privacy Mode',
                                         'Are you sure you want to disable privacy mode?',
                                         QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.mouse_tracker.set_privacy_mode(new_mode)
            else:
                self.privacy_mode.setChecked(True)
        else:
            self.mouse_tracker.set_privacy_mode(new_mode)

    def toggle_track_mouse_x(self):
        if self.track_mouse_x.isChecked():
            self.frame_22.show()
        else:
            self.frame_22.hide()

    def toggle_track_mouse_y(self):
        if self.track_mouse_y.isChecked():
            self.frame_23.show()
        else:
            self.frame_23.hide()

    def change_collection(self):
        self.ImageGallery.blockSignals(True)
        self.ImageGallery.change_collection(self.collection.currentText())
        self.update_viewer(self.current_files, update_gallery=True)
        self.ImageGallery.blockSignals(False)
        # print(self.ImageGallery.currentIndex())
        if self.ImageGallery.currentIndex() > -1:
            self.change_settings_gallery(self.ImageGallery.currentIndex())

    def retry_load(self):
        QtCore.QTimer.singleShot(500, lambda: self.update_viewer(self.current_files))
        # self.update_viewer(self.current_files, update_gallery=True)

    def update_div_count(self, count):
        self.div_count.setText(count)

    def show_model_photo_mode(self):
        if not self.photoAvatarBody.isChecked() and not self.photoAvatarFace.isChecked():
            sender = self.sender()
            sender.setChecked(True)

    def being_edited(self):
        last = copy.deepcopy(self.edited)
        last_2 = copy.deepcopy(self.photoMode)

        if self.tabWidget_2.currentIndex() == 0 or not self.transparency.isChecked():
            self.edited = None
            self.photoMode = None
        elif self.tabWidget_2.currentIndex() == 2:
            self.edited = None
            self.photoMode = {
                "avatar": {
                    "body": self.photoAvatarBody.isChecked(),
                    "face": self.photoAvatarFace.isChecked()
                },
                "eyes": "photo_blinking_open" if self.photoEyesOpen.isChecked() else "photo_blinking_closed",
                "mouth": 0 if self.photoMouthClosed.isChecked() else 1 if self.photoMouthOpen.isChecked() else 2,
                "filters": self.photoFiltersEnabled.isChecked(),
                "shadows": self.photoShadowsEnabled.isChecked(),
                "css": self.photoCSSEnabled.isChecked(),
                "animations": self.photoAnimationsEnabled.isChecked()
            }
        else:
            current = self.SettingsGallery.currentWidget()
            if current is not None:
                result = current.accessibleName()
                if result == "General Settings":
                    self.edited = {
                        "type": "general",
                        "value": self.SettingsGallery.page,
                        "collection": self.collection.currentText()
                    }
                else:
                    self.edited = {"type": "layer", "value": result, "collection": None}
            else:
                self.edited = {"type": "layer", "value": None, "collection": None}
            self.photoMode = None
        self.audioStatus()
        if last != self.edited or last_2 != self.photoMode:
            QtCore.QTimer.singleShot(500, lambda: self.update_viewer(self.current_files, update_gallery=False))
        self.showUI()

    def check_for_update(self):
        try:
            latest_tag, data = self.get_latest_release_tag(repo_owner, repo_name)
        except TypeError:
            return

        if latest_tag:
            comparison_result = compare_versions(current_version, latest_tag)
            if not comparison_result:
                dialog = UpdateDialog(latest_tag, data, self)
                result = dialog.exec()
                print(result)
                if result:
                    reboot_dialog = QtWidgets.QMessageBox(self)
                    reboot_dialog.setWindowTitle("Update Complete")
                    reboot_dialog.setText("Update has been completed. Please restart the program.")
                    reboot_dialog.setIcon(QtWidgets.QMessageBox.Icon.Information)
                    reboot_dialog.exec()

                    self.close()

    def get_latest_release_tag(self, repo_owner, repo_name):
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data['tag_name'], data
            else:
                return None
        except BaseException:
            return None

    def mouse_tracking_changed(self):
        if self.mouseTrackingToggle.isChecked():
            self.mouse_tracker.set_tracking_mode("mouse")
            if not self.mouse_tracker._running:
                self.mouse_tracker.start()
            if not self.forced_mouse_tracker._running:
                self.forced_mouse_tracker.start()
            self.frame_34.show()
            self.frame_25.show()
            self.frame_42.hide()
            self.frame_37.show()
            self.cameraFeedFrame.hide()

            self.scale_camera_x.hide()
            self.scale_x.show()
            self.scale_camera_y.hide()

            self.scale_random_x.hide()
            self.scale_random_y.hide()

            self.scale_y.show()
            self.frame_56.hide()
        elif self.faceTrackingToggle.isChecked():
            self.mouse_tracker.set_tracking_mode("face")
            if not self.mouse_tracker._running:
                self.mouse_tracker.start()
            if not self.forced_mouse_tracker._running:
                self.forced_mouse_tracker.start()
            self.frame_37.show()
            self.frame_42.show()
            self.frame_34.show()
            self.frame_25.show()
            self.cameraFeedFrame.show()

            self.scale_camera_x.show()
            self.scale_x.hide()
            self.scale_camera_y.show()

            self.scale_random_x.hide()
            self.scale_random_y.hide()

            self.scale_y.hide()
            self.frame_56.hide()
        elif self.randomTrackingToggle.isChecked():
            self.mouse_tracker.set_tracking_mode("random")
            if not self.mouse_tracker._running:
                self.mouse_tracker.start()
            if not self.forced_mouse_tracker._running:
                self.forced_mouse_tracker.start()
            self.frame_34.show()
            self.frame_25.show()
            self.frame_42.hide()
            self.frame_37.show()
            self.cameraFeedFrame.hide()

            self.scale_camera_x.hide()
            self.scale_x.hide()
            self.scale_camera_y.hide()

            self.scale_random_x.show()
            self.scale_random_y.show()
            self.scale_y.hide()
            self.frame_56.show()
        else:
            if self.mouse_tracker._running:
                self.mouse_tracker.stop()
            if self.forced_mouse_tracker._running:
                self.forced_mouse_tracker.stop()
            self.frame_42.hide()
            self.frame_37.hide()
            self.frame_34.hide()
            self.frame_25.hide()
            self.cameraFeedFrame.hide()
            self.frame_56.hide()
        self.on_mouse_position_changed({"x": 0, "y": 0})
        self.update_settings()

    def change_audio_engine(self):
        engine_selected = self.audio_engine.currentText()

        if engine_selected == "pyaudio":
            self.frame_28.hide()
        else:
            self.frame_28.show()

        self.audio.change_audio_engine(engine_selected)
        self.update_settings()

    def change_noise_reduction(self):
        noise_reduction = self.noise_reduction.isChecked()

        if not noise_reduction:
            self.frame_36.hide()
        else:
            self.frame_36.show()

        self.audio.toggle_noise_reduction(noise_reduction)
        self.update_settings()

    def change_sample_rate(self):
        self.audio.change_sample_rate_noise_reduction(self.sample_rate.value())
        self.update_settings()

    def on_mouse_position_changed(self, position):
        if self.viewer.is_loaded:

            x = int(
                (
                    position['x'] * -1 if self.invert_mouse_x.isChecked() else position['x']
                ) if self.track_mouse_x.isChecked() else 0
            )
            y = int(
                (
                    position['y'] * -1 if self.invert_mouse_y.isChecked() else position['y']
                ) if self.track_mouse_y.isChecked() else 0
            )
            # z = int(position.get('z', 0.0000))

            if self.faceTrackingToggle.isChecked():
                scale_x = self.scale_camera_x.value()
                scale_y = self.scale_camera_y.value()
            elif self.randomTrackingToggle.isChecked():
                scale_x = self.scale_random_x.value()
                scale_y = self.scale_random_y.value()
            else:
                scale_x = self.scale_x.value()
                scale_y = self.scale_y.value()

            scaled_x = x * scale_x
            scaled_y = y * scale_y

            if self.faceTrackingToggle.isChecked():
                if self.auto_flip.isChecked():
                    offset = self.flip_camera_x.value()
                    if scaled_x >= offset:
                        self.flipCanvasToggleH.setChecked(False)
                    elif scaled_x <= -offset:
                        self.flipCanvasToggleH.setChecked(True)

            if self.randomTrackingToggle.isChecked():
                match self.status_audio:
                    case 0:
                        if not self.move_idle_random.isChecked():
                            scaled_x = 0
                            scaled_y = 0
                    case 1:
                        if not self.move_talking_random.isChecked():
                            scaled_x = 0
                            scaled_y = 0
                    case 2:
                        if not self.move_screaming_random.isChecked():
                            scaled_x = 0
                            scaled_y = 0

            pacing = self.tracking_position_pacing.currentText()
            speed = self.speed_movement.value()

            self.viewer.runJavaScript(
                f"try{{cursorPosition({scaled_x}, {scaled_y}, 0, '{pacing}', {speed});}}catch(e){{}}"""
            )
            if hasattr(self, 'hidden_window'):
                if self.second_window_toggle.isChecked():
                    self.hidden_window.viewer.page().runJavaScript(
                        f"try{{cursorPosition({scaled_x}, {scaled_y}, 0, '{pacing}', {speed});}}catch(e){{}}"""
                    )

            self.label_28.setText(f"X: {scaled_x}, Y: {scaled_y*-1} (Scaled)")
            self.label_19.setText(f"X: {x}, Y: {y*-1}")

    def on_mouse_position_forced(self, position):
        if self.viewer.is_loaded:
            x = int((position['x'] * -1 if self.invert_mouse_x.isChecked() else position['x']) if self.track_mouse_x.isChecked() else 0)
            y = int((position['y'] * -1 if self.invert_mouse_y.isChecked() else position['y']) if self.track_mouse_y.isChecked() else 0)

            scaled_x = x * self.scale_x.value()
            scaled_y = y * self.scale_y.value()

            pacing = self.tracking_position_pacing.currentText()
            speed = self.speed_movement.value()

            self.viewer.runJavaScript(
                f"try{{cursorPosition({scaled_x}, {scaled_y}, 1, '{pacing}', {speed});}}catch(e){{}}"""
            )
            if hasattr(self, 'hidden_window'):
                if self.second_window_toggle.isChecked():
                    self.hidden_window.viewer.page().runJavaScript(
                        f"try{{cursorPosition({scaled_x}, {scaled_y}, 1, '{pacing}', {speed});}}catch(e){{}}"""
                    )

    def on_zoom_delta_changed(self):
        if self.viewer.is_loaded:
            self.viewer.runJavaScript(f"document.body.style.zoom = '{self.generalScale.value()}%';""")
            if hasattr(self, 'hidden_window'):
                if self.second_window_toggle.isChecked():
                    self.hidden_window.viewer.page().runJavaScript(f"document.body.style.zoom = '{self.generalScale.value()}%';""")
        self.scaleValue.setText(f"{self.generalScale.value()}")

    def update_animations(self, default=None):
        if default is None:
            default = self.settings["animations"]

        self.animations_list = self.viewer.get_animations(self.anim_file)

        self.idle_animation.clear()
        self.talking_animation.clear()
        self.screaming_animation.clear()

        for animation in self.animations_list:
            self.idle_animation.addItem(animation)
            self.talking_animation.addItem(animation)
            self.screaming_animation.addItem(animation)

        self.load_animations(default)

    def load_animations(self, default=None):
        self.idle_animation.setCurrentText(default["idle"]["name"])
        self.talking_animation.setCurrentText(default["talking"]["name"])
        self.screaming_animation.setCurrentText(default.get("screaming", default["talking"])["name"])

        self.idle_speed.setValue(default["idle"]["speed"])
        self.talking_speed.setValue(default["talking"]["speed"])
        self.screaming_speed.setValue(default.get("screaming", default["talking"])["speed"])

        self.idle_animation_easing.setCurrentText(default["idle"].get("easing", "EaseInOut"))
        self.talking_animation_easing.setCurrentText(default["talking"].get("easing", "EaseInOut"))
        self.screaming_animation_easing.setCurrentText(default.get("screaming", default["talking"]).get("easing", "EaseInOut"))

        self.idle_animation_direction.setCurrentText(default["idle"].get("direction", "normal"))
        self.talking_animation_direction.setCurrentText(default["talking"].get("direction", "normal"))
        self.screaming_animation_direction.setCurrentText(default.get("screaming", default["talking"]).get("direction", "normal"))

        self.idle_animation_iteration.setValue(default["idle"].get("iteration", 0))
        self.talking_animation_iteration.setValue(default["talking"].get("iteration", 0))
        self.screaming_animation_iteration.setValue(default.get("screaming", default["talking"]).get("iteration", 0))

        if default is not None:
            self.update_settings()

    def update_hw_acceleration(self):
        self.update_settings()
        self.viewer.update_settings(hw_acceleration=self.settings.get("hardware acceleration", False))
        if self.second_window_toggle.isChecked():
            self.hidden_window.viewer.update_settings(hw_acceleration=self.settings.get("hardware acceleration", False))

    def flipCanvas(self):
        self.viewer.runJavaScript(
            f"flip_canvas({180 if self.flipCanvasToggleH.isChecked() else 0}, "
            f"{180 if self.flipCanvasToggleV.isChecked() else 0},"
            f"{self.flip_animation_speed.value()}, "
            f"'{self.flip_animation_pacing.currentText()}')"
        )
        if hasattr(self, 'hidden_window'):
            if self.second_window_toggle.isChecked():
                self.hidden_window.viewer.page().runJavaScript(
                    f"flip_canvas({180 if self.flipCanvasToggleH.isChecked() else 0}, "
                    f"{180 if self.flipCanvasToggleV.isChecked() else 0},"
                    f"{self.flip_animation_speed.value()}, "
                    f"'{self.flip_animation_pacing.currentText()}')"
                )

    def change_max_reference_volume(self):
        self.audio.change_max_reference_volume(new_value=self.reference_volume.value())
        self.update_settings()

    def start_twitch_connection(self, values, starting=False):
        if not starting:
            if (
                    values["APP_ID"] == self.twitch_api_client and
                    values["APP_SECRET"] == self.twitch_api_secret and
                    values.get("APP_USER", None) == self.twitch_user
            ):
                return
            else:
                with open(self.apiKeys, "w") as f:
                    json.dump({
                      "twitch": {
                        "user": values.get("APP_USER", None),
                        "client": values["APP_ID"],
                        "secret": values["APP_SECRET"]
                      }
                    }, f, indent=4, ensure_ascii=False)
                self.twitch_api_client = values["APP_ID"]
                self.twitch_api_secret = values["APP_SECRET"]
                self.twitch_user = values.get("APP_USER", None)

        if values["APP_ID"] is None or values["APP_SECRET"] is None:
            return

        self.TwitchAPI = TwitchAPI(
            APP_ID=values["APP_ID"],
            APP_SECRET=values["APP_SECRET"],
            APP_USER=values.get("APP_USER", None),
            res_dir=res_dir
        )
        self.TwitchAPI.event_signal.connect(self.shortcut_received)
        self.TwitchAPI.start()
        self.get_shortcuts()

    def update_viewer_files(self):
        settings_worker = Worker(self.update_settings_thread)
        settings_worker.signals.finished.connect(self.reload_page)
        self.threadpool.start(settings_worker)

    def reload_images(self):
        self.update_viewer(self.current_files, update_gallery=True)
        self.audioStatus(0)

    def reload_page(self):
        self.viewer.reload()
        if hasattr(self, 'hidden_window'):
            if self.second_window_toggle.isChecked():
                self.hidden_window.viewer.reload()
        self.update_viewer(self.current_files, update_gallery=True)
        self.audioStatus(0)

    def update_viewer_files_thread(self):
        try:
            with open(self.js_file, "w") as f:
                f.write(self.jsCode.toPlainText())
        except FileNotFoundError:
            pass

        try:
            with open(self.css_file, "w") as f:
                f.write(self.cssCode.toPlainText())
        except FileNotFoundError:
            pass

        try:
            with open(self.anim_file, "w") as f:
                f.write(self.animCode.toPlainText())
        except FileNotFoundError:
            pass

        try:
            with open(self.html_file, "w") as f:
                f.write(self.htmlCode.toPlainText())
        except FileNotFoundError:
            pass

    def restore_defaults(self):
        copy_file(self.js_file_default, self.js_file)
        copy_file(self.css_file_default, self.css_file)
        copy_file(self.anim_file_default, self.anim_file)
        copy_file(self.html_file_default, self.html_file)

        try:
            with open(self.js_file, "r") as f:
                self.jsCode.setPlainText(f.read())
        except FileNotFoundError:
            pass

        try:
            with open(self.css_file, "r") as f:
                self.cssCode.setPlainText(f.read())
        except FileNotFoundError:
            pass

        try:
            with open(self.anim_file, "r") as f:
                self.animCode.setPlainText(f.read())
        except FileNotFoundError:
            pass

        self.update_viewer(self.current_files, update_gallery=True)

    def toggle_editor(self):
        if self.editor.isHidden():
            self.hideUI_(True)
            self.editor.show()
        else:
            self.editor.hide()
            self.showUI(True)

    def change_settings_gallery(self, index):
        self.SettingsGallery.change_page(self.ImageGallery.itemText(index))

    def clearSelection(self):
        self.current_files = []
        self.update_viewer(self.current_files, update_gallery=True, update_settings=True)

    def load_settings(self):
        self.comboBox.setCurrentIndex(self.settings.get("background color", 0))
        self.PNGmethod.setCurrentIndex(self.settings.get("export mode", 0))
        self.HideUI.setChecked(self.settings.get("hide UI", True))
        self.windowAnimations.setChecked(self.settings.get("animations UI", True))
        self.generalScale.setValue(self.settings.get("general_scale", 100))
        self.scaleValue.setText(f"{self.generalScale.value()}")
        self.audio_engine.setCurrentText(self.settings.get("audio engine", "pyaudio"))
        self.mouseTrackingToggle.setChecked(self.settings.get("mouse tracking", "mouse") == "mouse")
        self.faceTrackingToggle.setChecked(self.settings.get("mouse tracking", "mouse") == "face")
        self.randomTrackingToggle.setChecked(self.settings.get("mouse tracking", "mouse") == "random")
        self.disableTrackingToggle.setChecked(self.settings.get("mouse tracking", "mouse") == "disabled")
        self.hw_acceleration.setChecked(self.settings.get("hardware acceleration", True))
        self.track_mouse_x.setChecked(self.settings.get("track_mouse_x", True))
        self.track_mouse_y.setChecked(self.settings.get("track_mouse_y", True))
        self.invert_mouse_x.setChecked(self.settings.get("invert_mouse_x", True))
        self.invert_mouse_y.setChecked(self.settings.get("invert_mouse_y", True))
        self.performance.setChecked(self.settings.get("performance", False))
        self.second_window_toggle.setChecked(self.settings.get("second_window_toggle", False))
        self.cameraSelector.setValue(self.settings.get("camera", 0))
        self.alphaSelector.setValue(self.settings.get("target_fps", 20))
        self.speed_movement.setValue(self.settings.get("speed_movement", 0.1))
        self.privacy_mode.setChecked(self.settings.get("privacy", True))
        self.scale_x.setValue(self.settings.get("scale_x", 1))
        self.scale_camera_x.setValue(self.settings.get("scale_camera_x", 100))
        self.scale_y.setValue(self.settings.get("scale_y", 1))

        self.general_shadow = self.settings.get("shadow", None)
        if self.general_shadow is not None:
            self.shadow_toggle.setChecked(True)
            self.color_selector.setText(self.general_shadow["shadowColor"])
            self.shadowBlur.setValue(self.general_shadow["shadowBlur"])
            self.shadowX.setValue(self.general_shadow["shadowX"])
            self.shadowY.setValue(self.general_shadow["shadowY"])
        else:
            self.shadow_toggle.setChecked(False)
            self.color_selector.setText("0, 0, 0, 255")
            self.shadowBlur.setValue(0)
            self.shadowX.setValue(0)
            self.shadowY.setValue(0)

        self.general_filters = self.settings.get("filters", None)
        if self.general_filters is not None:
            self.filters_toggle.setChecked(True)
            self.hue.setValue(self.general_filters["hue"]),
            self.saturation.setValue(self.general_filters["saturation"]),
            self.brightness.setValue(self.general_filters["brightness"]),
            self.contrast.setValue(self.general_filters["contrast"]),
            self.opacity.setValue(self.general_filters["opacity"]),
            self.blur.setValue(self.general_filters["blur"]),
            self.grayscale.setValue(self.general_filters["grayscale"]),
            self.invert.setValue(self.general_filters["invert"]),
            self.sepia.setValue(self.general_filters["sepia"])
        else:
            self.filters_toggle.setChecked(False)
            self.hue.setValue(0.0)
            self.saturation.setValue(100.0)
            self.brightness.setValue(100.0)
            self.contrast.setValue(100.0)
            self.opacity.setValue(100.0)
            self.blur.setValue(0.0)
            self.grayscale.setValue(0.0)
            self.invert.setValue(0.0)
            self.sepia.setValue(0.0)

        self.tracking_position_pacing.setCurrentText(self.settings.get("tracking_position_pacing", "Linear"))

        self.scale_camera_y.setValue(self.settings.get("scale_camera_y", 5))
        self.scale_random_x.setValue(self.settings.get("scale_random_x", 100))
        self.scale_random_y.setValue(self.settings.get("scale_random_y", 100))

        self.opacity_speed.setValue(self.settings.get("opacity_speed", 0.0)),

        self.move_idle_random.setChecked(self.settings.get("move_idle_random", False))
        self.move_talking_random.setChecked(self.settings.get("move_talking_random", True))
        self.move_screaming_random.setChecked(self.settings.get("move_screaming_random", True))

        self.flip_animation_speed.setValue(self.settings.get("flip_animation_speed", 0.5000))
        self.flip_animation_pacing.setCurrentText(self.settings.get("flip_animation_pacing", "ease-in-out"))

        self.local_obs_source_toggle.setChecked(self.settings.get("local_obs_source_toggle", False))
        self.remote_obs_source_toggle.setChecked(self.settings.get("remote_obs_source_toggle", False))
        self.remoteTalkDelay.setValue(self.settings.get("remoteTalkDelay", 0))

        self.webSocketToggle.setChecked(self.settings.get("websocket", False))
        self.webSocketPort.setValue(self.settings.get("websocket_port", 8765))

        self.local_canvas_source_toggle.setChecked(self.settings.get("local_canvas_source_toggle", True))

        self.auto_flip.setChecked(self.settings.get("auto_flip", False))
        self.flip_camera_x.setValue(self.settings.get("flip_camera_x", 1000))

        self.noise_reduction.setChecked(self.settings.get("noise_reduction", True))
        self.sample_rate.setValue(self.settings.get("sample_rate", 44100))

        collection = self.settings.get("collection", None)
        if collection is None:
            self.collection.setCurrentIndex(0)
        else:
            if collection in self.collections:
                self.collection.setCurrentText(collection)
            else:
                self.collection.setCurrentIndex(0)

    def update_settings(self):
        settings_worker = Worker(self.update_settings_thread)
        self.threadpool.start(settings_worker)
        self.audioStatus(0)

    def update_settings_thread(self):
        mouse_tracking = "disabled"
        if self.mouseTrackingToggle.isChecked():
            mouse_tracking = "mouse"
        elif self.faceTrackingToggle.isChecked():
            mouse_tracking = "face"
        elif self.randomTrackingToggle.isChecked():
            mouse_tracking = "random"

        self.settings = {
            "volume threshold": self.audio.volume.value(),
            "scream threshold": self.audio.volume_scream.value(),
            "delay threshold": self.audio.delay.value(),
            "delay threshold screaming": self.audio.delay_2.value(),
            "microphone selection": self.audio.microphones.currentIndex(),
            "microphone mute": self.audio.mute.isChecked(),
            "background color": self.comboBox.currentIndex(),
            "export mode": self.PNGmethod.currentIndex(),
            "hide UI": self.HideUI.isChecked(),
            "animations UI": self.windowAnimations.isChecked(),
            "max_reference_volume": self.reference_volume.value(),
            "general_scale": self.generalScale.value(),
            "animations": {
                "idle": {
                    "name": self.idle_animation.currentText(),
                    "speed": self.idle_speed.value(),
                    "iteration": self.idle_animation_iteration.value(),
                    "easing": self.idle_animation_easing.currentText(),
                    "direction": self.idle_animation_direction.currentText()
                },
                "talking": {
                    "name": self.talking_animation.currentText(),
                    "speed": self.talking_speed.value(),
                    "iteration": self.talking_animation_iteration.value(),
                    "easing": self.talking_animation_easing.currentText(),
                    "direction": self.talking_animation_direction.currentText()
                },
                "screaming": {
                    "name": self.screaming_animation.currentText(),
                    "speed": self.screaming_speed.value(),
                    "iteration": self.screaming_animation_iteration.value(),
                    "easing": self.screaming_animation_easing.currentText(),
                    "direction": self.screaming_animation_direction.currentText()
                }
            },
            "audio engine": self.audio_engine.currentText(),
            "mouse tracking": mouse_tracking,
            "hardware acceleration": self.hw_acceleration.isChecked(),
            "track_mouse_x": self.track_mouse_x.isChecked(),
            "track_mouse_y": self.track_mouse_y.isChecked(),
            "invert_mouse_x": self.invert_mouse_x.isChecked(),
            "invert_mouse_y": self.invert_mouse_y.isChecked(),
            "performance": self.performance.isChecked(),
            "second_window_toggle": self.second_window_toggle.isChecked(),
            "collection": self.collection.currentText(),
            "flip_animation_speed": self.flip_animation_speed.value(),
            "flip_animation_pacing": self.flip_animation_pacing.currentText(),

            "opacity_speed": self.opacity_speed.value(),

            "camera": self.cameraSelector.value(),
            "target_fps": self.alphaSelector.value(),
            "speed_movement": self.speed_movement.value(),
            "privacy": self.privacy_mode.isChecked(),
            "scale_x": self.scale_x.value(),
            "scale_camera_x": self.scale_camera_x.value(),
            "scale_y": self.scale_y.value(),
            "scale_camera_y": self.scale_camera_y.value(),

            "tracking_position_pacing": self.tracking_position_pacing.currentText(),

            "move_idle_random": self.move_idle_random.isChecked(),
            "move_talking_random": self.move_talking_random.isChecked(),
            "move_screaming_random": self.move_screaming_random.isChecked(),

            "scale_random_x": self.scale_random_x.value(),
            "scale_random_y": self.scale_random_y.value(),

            "noise_reduction": self.noise_reduction.isChecked(),
            "sample_rate": self.sample_rate.value(),

            "websocket": self.webSocketToggle.isChecked(),
            "websocket_port": self.webSocketPort.value(),

            "local_canvas_source_toggle": self.local_canvas_source_toggle.isChecked(),

            "local_obs_source_toggle": self.local_obs_source_toggle.isChecked(),
            "remote_obs_source_toggle": self.remote_obs_source_toggle.isChecked(),
            "remoteTalkDelay": self.remoteTalkDelay.value(),

            "filters": self.general_filters,
            "shadow": self.general_shadow,

            "auto_flip": self.auto_flip.isChecked(),
            "flip_camera_x": self.flip_camera_x.value(),
        }
        self.save_parameters_to_json()

    def delete_shortcut(self, value):
        self.file_parameters_default[value['route']]["hotkeys"] = copy.deepcopy(value["hotkeys"])
        self.file_parameters_current[value['route']]["hotkeys"] = copy.deepcopy(value["hotkeys"])
        self.save_parameters_to_json()
        self.get_shortcuts()

    def get_shortcuts(self):
        midi = []
        keyboard = []
        twitch = {
            "TwitchReward": [],
            "TwitchFollow": [],
            "TwitchCheer": [],
            "TwitchRaid": [],
            "TwitchSub": [],
            "TwitchGiftedSub": [],
            "TwitchChatMessage": []
        }

        for root, dirs, files in os.walk(os.path.join(res_dir, "Models")):
            for filename in files:
                if filename == "data.json":
                    data_json_path = os.path.join(root, filename)
                    with open(data_json_path, 'r') as json_file:
                        data = json.load(json_file)
                        shortcuts = data.get("shortcuts", None)
                        for shortcut in shortcuts:
                            if shortcut["type"] == "Keyboard":
                                command = {
                                    "path": data_json_path.replace("data", "model"),
                                    "type": "Model", "command": shortcut["command"], "mode": shortcut["mode"]
                                }
                                if "time" in shortcut:
                                    command["time"] = shortcut["time"]
                                keyboard.append(command)
                            elif shortcut["type"] == "Midi":
                                command = {
                                    "path": data_json_path.replace("data", "model"), "type": "Model",
                                    "command": mido.Message.from_dict(shortcut["command"]), "mode": shortcut["mode"]
                                }
                                if "time" in shortcut:
                                    command["time"] = shortcut["time"]
                                midi.append(command)
                            else:
                                command = {
                                    "path": data_json_path.replace("data", "model"), "type": "Model",
                                    "command": shortcut, "mode": shortcut["mode"]
                                }
                                if "time" in shortcut:
                                    command["time"] = shortcut["time"]
                                twitch[shortcut["type"]].append(command)

        for route, shortcut in self.file_parameters_current.get_shortcuts():
            if shortcut["type"] == "Keyboard":
                keyboard.append({
                    "path": route, "type": "Asset", "mode": shortcut["mode"],
                    "command": shortcut["command"]
                })
            elif shortcut["type"] == "Midi":
                midi.append(
                    {"path": route, "type": "Asset", "mode": shortcut["mode"],
                     "command": mido.Message.from_dict(shortcut["command"])}
                )
            else:
                twitch[shortcut["type"]].append({
                    "path": route, "type": "Asset", "mode": shortcut["mode"],
                    "command": shortcut
                })
        self.midi_listener.update_shortcuts(midi)
        self.keyboard_listener.update_shortcuts(keyboard)
        if self.TwitchAPI is not None:
            self.TwitchAPI.update_shortcuts(twitch)

    def changePage(self, index):
        self.stackedWidget.setCurrentIndex(index)
        self.donationBtnURL.setCurrentIndex(index)
        self.tabWidget.setCurrentIndex(index)
        if self.tabWidget_2.currentIndex() == 1:
            self.update_viewer(self.current_files, update_settings=True)
        self.being_edited()

    def deselect_every_asset(self):
        self.current_files = []
        self.update_viewer(self.current_files, update_settings=self.tabWidget_2.currentIndex() == 1)

    def handle_assets_command_disaable(self, command, shortcuts):
        if command["mode"] in ["toggle", "disable"]:
            self.current_files.remove(shortcuts["path"])

        elif command["mode"] == "timer":
            disable_shortcuts = copy.deepcopy(command)
            disable_shortcuts["mode"] = "disable"
            self.shortcut_received(disable_shortcuts)
            enable_shortcuts = copy.deepcopy(command)
            enable_shortcuts["mode"] = "enable"
            QtCore.QTimer.singleShot(command["time"], lambda x=enable_shortcuts: self.shortcut_received(x))

    def handle_assets_command_enable(self, command, shortcuts):
        if command["mode"] in ["toggle", "enable"]:
            self.current_files.append(shortcuts["path"])
        elif command["mode"] == "timer":
            enable_shortcuts = copy.deepcopy(command)
            enable_shortcuts["mode"] = "enable"
            self.shortcut_received(enable_shortcuts)
            disable_shortcuts = copy.deepcopy(command)
            disable_shortcuts["mode"] = "disable"
            QtCore.QTimer.singleShot(
                command["time"],
                lambda x=disable_shortcuts: self.shortcut_received(x)
            )

    def shortcut_received(self, shortcuts):
        if shortcuts["type"] == "Model":
            if shortcuts["mode"] == "timer":
                enable_shortcuts = copy.deepcopy(shortcuts)
                enable_shortcuts["mode"] = "enable"
                self.shortcut_received(enable_shortcuts)
                disable_shortcuts = copy.deepcopy(shortcuts)
                disable_shortcuts["mode"] = "disable"
                QtCore.QTimer.singleShot(int(shortcuts["time"]), lambda x=disable_shortcuts: self.shortcut_received(x))
            else:
                parts = shortcuts["path"].split(os.path.sep)
                print(parts)
                self.load_model({"name": parts[-2], "type": parts[-3]}, mode=shortcuts["mode"])

        elif shortcuts["type"] == "Asset":
            if shortcuts["path"] in self.current_files:
                if self.file_parameters_default[shortcuts["path"]]:
                    for command in self.file_parameters_default[shortcuts["path"]]["hotkeys"]:
                        print(command)
                        if (
                                (isinstance(shortcuts["command"], str) and shortcuts["command"] != "WebSocket")
                                or isinstance(shortcuts["command"], list)
                        ) and command["command"] == shortcuts["command"] and command["type"] == shortcuts["source"]:
                            self.handle_assets_command_disaable(command, shortcuts)
                        elif ("command" in shortcuts["command"] and command["command"] ==
                              shortcuts["command"]["command"] and command["type"] == shortcuts["source"]):
                            self.handle_assets_command_disaable(command, shortcuts)
                        elif shortcuts["command"] == "WebSocket":
                            command = shortcuts
                            self.handle_assets_command_disaable(command, shortcuts)
                        elif command["command"] == shortcuts["command"] and command["type"] == shortcuts["source"]:
                            self.handle_assets_command_disaable(command, shortcuts)
            else:
                if self.file_parameters_default[shortcuts["path"]]:
                    for command in self.file_parameters_default[shortcuts["path"]]["hotkeys"]:
                        if ((isinstance(shortcuts["command"], str) and shortcuts["command"] != "WebSocket") or isinstance(shortcuts["command"], list)) and command["command"] == shortcuts["command"] and command["type"] == shortcuts["source"]:
                            self.handle_assets_command_enable(command, shortcuts)
                        elif "command" in shortcuts["command"] and command["command"] == shortcuts["command"]["command"] and command["type"] == shortcuts["source"]:
                            self.handle_assets_command_enable(command, shortcuts)
                        elif shortcuts["command"] == "WebSocket":
                            command = shortcuts
                            self.handle_assets_command_enable(command, shortcuts)
                        elif command["command"] == shortcuts["command"] and command["type"] == shortcuts["source"]:
                            self.handle_assets_command_enable(command, shortcuts)

            self.update_viewer(self.current_files, update_settings=self.tabWidget_2.currentIndex() == 1)
        else:
            print(f"Received: {shortcuts} System")

    def dialog_shortcut(self, data):
        dialog = ShortcutsDialog(
            midi_listener=self.midi_listener,
            keyboard_listener=self.keyboard_listener,
            twitch_listener=self.TwitchAPI,
            data=data, exe_dir=exe_dir
        )
        dialog.new_command.connect(self.create_shortcuts)
        dialog.exec()

    def create_shortcuts(self, data):
        if data["type"] in ["Avatars", "Expressions"]:
            mainFolder = str(os.path.join(res_dir, "Models", data['type']))
            with open(
                    os.path.join(mainFolder, data['name'], "data.json"), 'r'
            ) as json_file:
                old_data = json.load(json_file)
            old_data["shortcuts"] = copy.deepcopy(data['value']["hotkeys"])
            with open(
                    os.path.join(mainFolder, data['name'], "data.json"), 'w'
            ) as json_file:
                json.dump(old_data, json_file, indent=4, ensure_ascii=False)
            self.modelGallery.reload_models(self.savedAvatars)
        elif data["type"] in ["Assets"]:
            self.file_parameters_default[data['value']['route']]["hotkeys"] = copy.deepcopy(data['value']["hotkeys"])
            self.file_parameters_current[data['value']['route']]["hotkeys"] = copy.deepcopy(data['value']["hotkeys"])

            self.save_parameters_to_json()
            self.update_viewer(self.current_files, update_settings=True)
        self.get_shortcuts()

    def load_model(self, data, mode="enable"):
        if mode == "toggle":
            if data["type"] == "Avatars":
                if self.current_model["name"] != data["name"]:
                    self.load_model(data, mode="enable")
                else:
                    self.load_model(data, mode="disable")
            elif data["type"] == "Expressions":
                if self.current_expression["name"] != data["name"]:
                    self.load_model(data, mode="enable")
                else:
                    self.load_model(data, mode="disable")
            return

        if mode == "enable":
            self.last_model = copy.deepcopy(self.current_model)
            self.last_expression = copy.deepcopy(self.current_expression)

        if mode == "disable":
            if data["type"] == "Avatars":
                data = copy.deepcopy(self.last_model)
            elif data["type"] == "Expressions":
                data = copy.deepcopy(self.last_expression)

        with open(os.path.join(res_dir, "Models", data['type'], data['name'], "model.json"), "r") as load_file:
            files = json.load(load_file)
            for file in files:
                self.file_parameters_current[os.path.normpath(file["route"])] = \
                    {key: value for key, value in file.items() if key != "route"}

        current_files = []

        if data["type"] == "Avatars":
            for file in self.current_files:
                if self.check_if_expression(file):
                    current_files.append(file)

        elif data["type"] == "Expressions":
            for file in self.current_files:
                if not self.check_if_expression(file):
                    current_files.append(file)

        for file in files:
            current_files.append(os.path.normpath(file["route"]))

        self.update_viewer(current_files)
        if data["type"] == "Expressions":
            with open(os.path.join(res_dir, "Models", data['type'], data['name'], "data.json"), "r") as load_file:
                animations = json.load(load_file).get("animations", None)
                if animations is not None:
                    self.load_animations(default=animations)

        if data["type"] == "Avatars":
            self.current_model = copy.deepcopy(data)
        elif data["type"] == "Expressions":
            self.current_expression = copy.deepcopy(data)

    def check_if_expression(self, file):
        with open(os.path.join(res_dir, "Data", "expressionFolders.json"), "r") as expressions_list:
            for expression in json.load(expressions_list):
                if os.path.normpath(expression) in os.path.normpath(file):
                    return True
        return False

    def CreateCollection(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter new collection name:')

        if ok:
            if not text:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                msg.setText(f"Name of category can't be empty.")
                msg.setWindowTitle("Warning")
                msg.exec()
            elif os.path.exists(os.path.join(res_dir, "Assets", text.lower())):
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                msg.setText("Asset collection with this name already exists.")
                msg.setWindowTitle("Warning")
                msg.exec()
            else:
                os.mkdir(os.path.join(res_dir, "Assets", text.title()))
                self.collection.addItem(text.title())
                self.collection.setCurrentText(text.title())
                self.update_viewer(self.current_files, update_gallery=True)

    def CreateCategory(self):
        text, ok = QtWidgets.QInputDialog.getText(
            self, 'Input Dialog',
            f'Enter new category name for "{self.collection.currentText()}":'
        )

        if ok:
            if not text:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                msg.setText(f"Name of category can't be empty.")
                msg.setWindowTitle("Warning")
                msg.exec()
            elif os.path.exists(os.path.join(res_dir, "Assets", self.collection.currentText(), text.lower())):
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                msg.setText(f'Asset category with this name already exists in "{self.collection.currentText()}".')
                msg.setWindowTitle("Warning")
                msg.exec()
            elif text.lower() in [i.lower() for i in self.collections]:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                msg.setText(f"Asset can't be the same name as a collection.")
                msg.setWindowTitle("Warning")
                msg.exec()
            else:
                os.mkdir(os.path.join(res_dir, "Assets", self.collection.currentText(), text.title()))
                self.update_viewer(self.current_files, update_gallery=True)

    def OpenAssetsFolder(self):
        path = os.path.join(res_dir, "Assets")
        if sys.platform == 'darwin':
            subprocess.run(['open', path])
        elif sys.platform in ['linux', 'linux2']:
            subprocess.run(['xdg-open', path])
        elif sys.platform == 'win32':
            subprocess.run(['explorer', path])
        else:
            print("Unsupported operating system")

    def get_folders_in_assets(self):
        folder_path = os.path.join(res_dir, "Assets")
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            folders = [self.tr(f) for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
            return [self.tr("Select Category...")] + folders
        else:
            return [self.tr("Select Category...")]

    def save_avatar(self, model=None):
        if model is not None and model is not False:
            confirmation = QtWidgets.QMessageBox()
            confirmation.setIcon(QtWidgets.QMessageBox.Icon.Question)
            confirmation.setText("Are you sure you want to update this model?")
            confirmation.setWindowTitle("Confirmation")
            confirmation.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)

            result = confirmation.exec()

            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return

            modelName, ok = model, True
        else:
            modelName, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter new avatar name:')

        if ok:
            directory = os.path.join(res_dir, "Models", "Avatars", modelName)
            if model is None or model is False:
                if os.path.exists(directory):
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                    msg.setText("This Model name already exists.")
                    msg.setInformativeText("Please choose a different model name.")
                    msg.setWindowTitle("Model Exists")
                    msg.exec()
                    return
                else:
                    os.mkdir(directory)
            temp = "savingAvatar.png"

            files = [
                file for file in self.getFiles(self.current_files)
                if not any(route in file["route"] for route in self.expressionSelector.selected_folders)
            ]
            self.image_generator(output_name=temp, method=2, savingModel=1, custom_file_list=files)
            self.save_model(directory, modelName, temp, files)
            if model is None or model is False:
                self.modelGallery.add_model(modelName)
            else:
                self.modelGallery.reload_models(
                    [folder for folder in os.listdir(os.path.join(res_dir, "Models", "Avatars")) if "." not in folder])

    def save_expression(self, model=None):
        if model is not None and model is not False:
            confirmation = QtWidgets.QMessageBox()
            confirmation.setIcon(QtWidgets.QMessageBox.Icon.Question)
            confirmation.setText("Are you sure you want to update this model?")
            confirmation.setWindowTitle("Confirmation")
            confirmation.setStandardButtons(
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)

            result = confirmation.exec()

            if result != QtWidgets.QMessageBox.StandardButton.Yes:
                return

            modelName, ok = model, True
        else:
            modelName, ok = QtWidgets.QInputDialog.getText(self, 'Input Dialog', 'Enter new expression name:')

        if ok:
            directory = os.path.join(res_dir, "Models", "Expressions", modelName)
            if model is None or model is False:
                if os.path.exists(directory):
                    msg = QtWidgets.QMessageBox()
                    msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                    msg.setText("This Model name already exists.")
                    msg.setInformativeText("Please choose a different model name.")
                    msg.setWindowTitle("Model Exists")
                    msg.exec()
                    return
                else:
                    os.mkdir(directory)
            temp = "savingExpression.png"
            files = [
                file for file in self.getFiles(self.current_files)
                if any(route in file["route"] for route in self.expressionSelector.selected_folders)
            ]
            self.image_generator(output_name=temp, method=2, savingModel=2, custom_file_list=files)
            self.save_model(str(directory), modelName, temp, files)
            if model is None or model is False:
                self.expressionGallery.add_model(modelName)
            else:
                self.expressionGallery.reload_models(
                    [folder for folder in os.listdir(os.path.join(res_dir, "Models", "Expressions")) if "." not in folder])

    def save_model(self, directory, modelName, temp, files):
        self.ImageGallery.create_thumbnail(temp, custom_name=os.path.join(directory, "thumb.png"))
        os.remove(temp)
        with open(os.path.join(directory, "model.json"), "w") as file:
            json.dump(files, file, indent=4, ensure_ascii=False)

        data_file = os.path.normpath(os.path.join(directory, "data.json"))
        if os.path.exists(data_file):
            with open(data_file, "r") as file:
                data = json.load(file)
        else:
            data = None
        with open(data_file, "w") as file:
            data = {"shortcuts": [], "animations": {}} if data is None else data
            if "animations" not in data:
                data["animations"] = {}
            data["animations"] = {
                "idle": {
                    "name": self.idle_animation.currentText(),
                    "speed": self.idle_speed.value(),
                    "iteration": self.idle_animation_iteration.value(),
                    "easing": self.idle_animation_easing.currentText(),
                    "direction": self.idle_animation_direction.currentText()
                },
                "talking": {
                    "name": self.talking_animation.currentText(),
                    "speed": self.talking_speed.value(),
                    "iteration": self.talking_animation_iteration.value(),
                    "easing": self.talking_animation_easing.currentText(),
                    "direction": self.talking_animation_direction.currentText()
                },
                "screaming": {
                    "name": self.screaming_animation.currentText(),
                    "speed": self.screaming_speed.value(),
                    "iteration": self.screaming_animation_iteration.value(),
                    "pacing": self.screaming_animation_easing.currentText(),
                    "direction": self.screaming_animation_direction.currentText()
                }
            }
            json.dump(data, file, indent=4, ensure_ascii=False)

    def export_png(self):
        method = self.PNGmethod.currentIndex()
        if method == 0:
            return
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption=self.tr("Save File"),
            directory=str(Path.home()),
            filter=self.tr("Images (*.png)")
        )
        if fileName:
            if not fileName.lower().endswith(".png"):
                fileName += ".png"
            self.image_generator(output_name=fileName, method=method)

    def reboot_audio(self):
        self.audio.active_audio_signal = -1

    def save_canvas_image(self):
        self.viewer.runJavaScript("try{save_image()}catch{}")

    def audioStatus(self, status=0):
        self.status_audio = status
        try:
            if self.viewer.is_loaded:
                animation = self.selected_animations[status]["animation"].currentText()
                speed = self.selected_animations[status]["speed"].value()
                direction = self.selected_animations[status]["direction"].currentText()
                easing = self.selected_animations[status]["easing"].currentText()
                iteration = self.selected_animations[status]["iteration"].value()

                self.viewer.runJavaScript(
                    f'try{{update_mic('
                    f'{status if self.photoMode is None else self.photoMode["mouth"]}, '
                    f'"{animation if self.photoMode is None else animation if self.photoMode["animations"] else "None"}", '
                    f'{speed}, '
                    f'"{direction}", '
                    f'"{easing}", '
                    f'{iteration}, '
                    f'{"true" if self.performance.isChecked() else "false"}'
                    f')}}catch{{}}'
                )
                if hasattr(self, 'hidden_window'):
                    if self.second_window_toggle.isChecked():
                        self.hidden_window.viewer.page().runJavaScript(
                            f'try{{update_mic('
                            f'{status}, '
                            f'"{animation}", '
                            f'{speed}, '
                            f'"{direction}", '
                            f'"{easing}", '
                            f'{iteration}, '
                            f'{"true" if self.performance.isChecked() else "false"}'
                            f')}}catch{{}}'
                        )
        except AttributeError:
            pass

    def saveSettings_list(self, settings_list):
        for settings in settings_list:
            try:
                if settings['default']:
                    self.file_parameters_default[settings['value']['route']] = copy.deepcopy(settings["value"])
                    self.file_parameters_default[settings['value']['route']].pop("route")
                self.file_parameters_current[settings['value']['route']] = copy.deepcopy(settings["value"])
                self.file_parameters_current[settings['value']['route']].pop("route")
            except KeyError:
                pass
        self.update_viewer(self.current_files)

    def saveSettings(self, settings):
        if settings['default']:
            # self.file_parameters_default[settings['value']['route']] = copy.deepcopy(settings["value"])
            # self.file_parameters_default[settings['value']['route']].pop("route")
            pass
        self.file_parameters_current[settings['value']['route']] = copy.deepcopy(settings["value"])
        self.file_parameters_current[settings['value']['route']].pop("route")
        self.update_viewer(self.current_files)

    def save_parameters_to_json(self):
        # with open(self.json_file, "w") as f:
        #     json.dump(self.file_parameters_default, f, indent=4, ensure_ascii=False)

        with open(self.current_model_json_file, "w") as f:
            json.dump(self.current_model, f, indent=4, ensure_ascii=False)

        with open(self.current_json_file, "w") as f:
            json.dump(self.current_files, f, indent=4, ensure_ascii=False)

        with open(self.settings_json_file, "w") as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)

    def image_generator(self, output_name, method=1, savingModel=0, custom_file_list=None):
        files = self.getFiles(self.current_files) if custom_file_list is None else custom_file_list
        files = [
            i for i in files
            if i["blinking"] in ["ignore", "blinking_open"] and (
                    "ignore" in i["talking"] or "talking_closed" in i["talking"]
            )
        ]

        images = []

        if method == 1:
            size_counter = Counter()

            for file_data in files:
                file_route = os.path.join(res_dir, file_data["route"])
                rotation = file_data["rotation"]
                posZ = file_data["posZ"]
                posX = file_data["posX"]
                posY = file_data["posY"]
                sizeX = file_data["sizeX"]
                sizeY = file_data["sizeY"]

                if file_route.lower().endswith((".png", ".jpg", ".jpeg")):
                    image = Image.open(file_route)
                elif file_route.lower().endswith((".gif", ".webp")):
                    image = Image.open(file_route)

                    if isinstance(image, Image.Image):
                        frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
                        num_frames = len(frames)
                        middle_frame_index = num_frames // 2
                        image = frames[middle_frame_index]

                if rotation != 0:
                    image = image.rotate(rotation * -1, expand=True)

                if sizeX != image.width or sizeY != image.height:
                    image = image.resize((sizeX, sizeY))

                size_counter[(sizeX, sizeY)] += 1

                images.append((image, posZ, posX, posY))

            most_used_size = size_counter.most_common(1)[0][0]

            if images:
                images.sort(key=lambda x: x[1])

                canvas = Image.new("RGBA", (most_used_size[0], most_used_size[1]), (0, 0, 0, 0))

                for image, _, posX, posY in images:
                    canvas = Image.alpha_composite(
                        canvas, ImageOps.fit(
                            image, (most_used_size[0], most_used_size[1]), method=0, bleed=0.0, centering=(0.5, 0.5)
                        )
                    )

                canvas.save(output_name, "PNG")

        elif method == 2:
            for file_data in files:
                file_route = os.path.join(res_dir, file_data["route"])
                print(file_route)
                rotation = file_data["rotation"]
                posZ = file_data["posZ"]
                posX = file_data["posX"]
                posY = file_data["posY"]
                sizeX = file_data["sizeX"]
                sizeY = file_data["sizeY"]

                if file_route.lower().endswith((".png", ".jpg", ".jpeg")):
                    image = Image.open(file_route)
                elif file_route.lower().endswith((".gif", ".webp")):
                    image = Image.open(file_route)

                    if isinstance(image, Image.Image):
                        frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
                        num_frames = len(frames)
                        middle_frame_index = num_frames // 2
                        image = frames[middle_frame_index]

                if sizeX != image.width or sizeY != image.height:
                    image = image.resize((sizeX, sizeY))

                if rotation != 0:
                    image = image.rotate(rotation * -1, expand=True)

                center_x = self.width() // 2
                center_y = self.height() // 2

                adjusted_posX = center_x + posX - (image.width / 2)
                adjusted_posY = center_y + posY - (image.height / 2)

                images.append((image, posZ, adjusted_posX, adjusted_posY))

            if images:
                images.sort(key=lambda x: x[1])
                max_width, max_height = self.width(), self.height()
                canvas = Image.new("RGBA", (max_width, max_height))
                for image, _, posX, posY in images:
                    try:
                        canvas.paste(image, (int(posX), int(posY)), image)
                    except ValueError:
                        pass
                canvas.save(output_name, "PNG")

    def getFiles(self, files):
        images_list = []
        for file in files:
            if file in self.file_parameters_current:
                parameters = self.file_parameters_current[file]
            else:
                image = Image.open(os.path.join(res_dir, file))
                width, height = image.size
                parameters = {
                        "sizeX": width,
                        "sizeY": height,
                        "posX": 0,
                        "posY": 0,
                        "posZ": 0,
                        "blinking": "ignore",
                        "talking": "ignore",
                        "css": "",
                        "use_css": False,
                        "hotkeys": [],
                        "animation": [],
                        "rotation": 0,
                    }

                self.file_parameters_current[file] = parameters
            try:
                images_list.append({
                    "route": os.path.normpath(file),
                    **parameters
                })
            except TypeError:
                pass
        return images_list

    def update_viewer(self, files=None, update_gallery=False, update_settings=False):
        images_list = self.getFiles(files)

        if not update_settings:
            filtered_photo = copy.deepcopy(images_list)
            if self.photoMode is not None:
                if not self.photoMode["avatar"]["body"]:
                    filtered_photo = [
                        file for file in filtered_photo
                        if any(route in file["route"] for route in self.expressionSelector.selected_folders)
                    ]
                elif not self.photoMode["avatar"]["face"]:
                    filtered_photo = [
                        file for file in filtered_photo
                        if not any(route in file["route"] for route in self.expressionSelector.selected_folders)
                    ]

            self.viewer.updateImages(
                filtered_photo, self.color, self.generalScale.value(), self.edited, self.performance.isChecked(),
                filters=self.general_filters, shadow=self.general_shadow, photo_mode=self.photoMode
            )
            if hasattr(self, 'hidden_window'):
                if self.second_window_toggle.isChecked():
                    self.hidden_window.viewer.updateImages(
                        images_list, self.color, self.generalScale.value(), None, self.performance.isChecked(),
                        filters=self.general_filters, shadow=self.general_shadow
                    )
        if self.tabWidget_2.currentIndex() == 1:
            if self.current_files != files or update_settings:
                self.SettingsGallery.set_items(
                    images_list,
                    self.ImageGallery.itemText(self.ImageGallery.currentIndex())
                )
        if update_gallery:
            self.ImageGallery.load_images(files)
        else:
            self.ImageGallery.set_buttons_checked(files)
        self.current_files = files
        self.htmlCode.setPlainText(self.viewer.html_code)
        self.save_parameters_to_json()
        QtCore.QTimer.singleShot(500, self.audioStatus)

    def event(self, event):
        try:
            if event.type() == QtCore.QEvent.Type.HoverEnter:
                self.showUI()
            elif event.type() == QtCore.QEvent.Type.HoverMove and self.frame_4.isHidden():
                self.showUI()
            elif event.type() == QtCore.QEvent.Type.HoverLeave:
                self.hideUI_()
        except AttributeError:
            pass
        return super().event(event)

    def showUI(self, force=False):
        if self.HideUI.isChecked() or force:
            self.hidden_ui = False
            if self.windowAnimations.isChecked():
                self.group = QtCore.QParallelAnimationGroup()

                easingCurve = QEasingCurve.Type.OutCubic
                speed = 500

                if self.editor.isHidden():
                    animation_1 = QtCore.QVariantAnimation()
                    animation_1.setEasingCurve(easingCurve)
                    animation_1.setDuration(speed)
                    animation_1.valueChanged.connect(lambda value: self.animateGeometry(self.frame_4, value))
                    animation_1.setStartValue(self.frame_4.geometry())
                    animation_1.setEndValue(self.get_positions("frame_4"))
                    self.group.addAnimation(animation_1)

                    animation_2 = QtCore.QVariantAnimation()
                    animation_2.setEasingCurve(easingCurve)
                    animation_2.setDuration(speed)
                    if self.tabWidget_2.currentIndex() == 1:
                        if self.SettingsGallery.count() == 0:
                            animation_2.valueChanged.connect(lambda value: self.animateGeometry(self.frame_3, value))
                            animation_2.setStartValue(self.frame_3.geometry())
                            animation_2.setEndValue(self.get_positions("frame_3", True))
                            self.group.addAnimation(animation_2)
                        else:
                            animation_2.valueChanged.connect(lambda value: self.animateGeometry(self.frame_3, value))
                            animation_2.setStartValue(self.frame_3.geometry())
                            animation_2.setEndValue(self.get_positions("frame_3"))
                            self.group.addAnimation(animation_2)
                    else:
                        animation_2.valueChanged.connect(lambda value: self.animateGeometry(self.frame_3, value))
                        animation_2.setStartValue(self.frame_3.geometry())
                        animation_2.setEndValue(self.get_positions("frame_3"))
                    self.group.addAnimation(animation_2)

                    animation_3 = QtCore.QVariantAnimation()
                    animation_3.setEasingCurve(easingCurve)
                    animation_3.setDuration(speed)
                    animation_3.valueChanged.connect(lambda value: self.animateGeometry(self.donationBtnURL, value))
                    animation_3.setStartValue(self.donationBtnURL.geometry())
                    animation_3.setEndValue(self.get_positions("donationBtnURL"))
                    self.group.addAnimation(animation_3)

                    animation_4 = QtCore.QVariantAnimation()
                    animation_4.setEasingCurve(easingCurve)
                    animation_4.setDuration(speed)
                    animation_4.valueChanged.connect(lambda value: self.animateGeometry(self.editorFrame, value))
                    animation_4.setStartValue(self.editorFrame.geometry())
                    animation_4.setEndValue(self.get_positions("frame_3", True))
                    self.group.addAnimation(animation_4)

                if not self.editor.isHidden() or force:
                    self.editorFrame.show()
                    animation_4 = QtCore.QVariantAnimation()
                    animation_4.setEasingCurve(easingCurve)
                    animation_4.setDuration(speed)
                    animation_4.valueChanged.connect(lambda value: self.animateGeometry(self.editorFrame, value))
                    animation_4.setStartValue(self.editorFrame.geometry())
                    if force:
                        animation_4.setEndValue(self.get_positions("editor", True))
                    else:
                        animation_4.setEndValue(self.get_positions("editor"))
                    self.group.addAnimation(animation_4)

                self.group.start()
            else:
                self.editorFrame.setGeometry(self.get_positions("editor", self.hidden_ui))
                if self.editor.isHidden():
                    self.frame_4.show()
                    if self.tabWidget_2.currentIndex() == 1:
                        if self.edited is None or self.edited == {"type": "layer", "value": None}:
                            self.frame_3.hide()
                        else:
                            self.frame_3.show()
                    else:
                        self.frame_3.show()
                    self.donationBtnURL.show()
                if self.tabWidget_2.currentIndex() != 1:
                    if not self.editor.isHidden() or force:
                        if force:
                            self.editorFrame.hide()
                        else:
                            self.editorFrame.show()

    def hideUI_(self, force=False):
        if self.HideUI.isChecked() and self.tabWidget_2.currentIndex() != 1 or force:
            self.hidden_ui = True
            if self.windowAnimations.isChecked():
                self.group = QtCore.QParallelAnimationGroup()
                easingCurve = QEasingCurve.Type.InCubic
                speed = 500

                animation_1 = QtCore.QVariantAnimation()
                animation_1.setEasingCurve(easingCurve)
                animation_1.setDuration(speed)
                animation_1.valueChanged.connect(lambda value: self.animateGeometry(self.frame_4, value))
                animation_1.setStartValue(self.frame_4.geometry())
                animation_1.setEndValue(self.get_positions("frame_4", True))
                self.group.addAnimation(animation_1)

                animation_2 = QtCore.QVariantAnimation()
                animation_2.setEasingCurve(easingCurve)
                animation_2.setDuration(speed)
                animation_2.valueChanged.connect(lambda value: self.animateGeometry(self.frame_3, value))
                animation_2.setStartValue(self.frame_3.geometry())
                animation_2.setEndValue(self.get_positions("frame_3", True))
                self.group.addAnimation(animation_2)

                animation_3 = QtCore.QVariantAnimation()
                animation_3.setEasingCurve(easingCurve)
                animation_3.setDuration(speed)
                animation_3.valueChanged.connect(lambda value: self.animateGeometry(self.donationBtnURL, value))
                animation_3.setStartValue(self.donationBtnURL.geometry())
                animation_3.setEndValue(self.get_positions("donationBtnURL", True))
                self.group.addAnimation(animation_3)

                if not self.editor.isHidden() or force:
                    self.editorFrame.show()
                    animation_4 = QtCore.QVariantAnimation()
                    animation_4.setEasingCurve(easingCurve)
                    animation_4.setDuration(speed)
                    animation_4.valueChanged.connect(lambda value: self.animateGeometry(self.editorFrame, value))
                    animation_4.setStartValue(self.editorFrame.geometry())
                    if force:
                        animation_4.setEndValue(self.get_positions("editor"))
                    else:
                        animation_4.setEndValue(self.get_positions("editor", True))
                    self.group.addAnimation(animation_4)
                self.group.start()
            else:
                self.editorFrame.setGeometry(self.get_positions("frame_3", self.hidden_ui))
                self.frame_4.hide()
                self.frame_3.hide()
                self.donationBtnURL.hide()
                if self.tabWidget_2.currentIndex() != 1:
                    if self.editor.isHidden() or force:
                        if force:
                            self.editorFrame.show()
                        else:
                            self.editorFrame.hide()
        else:
            self.showUI(force)

    def setBGColor(self):
        match self.comboBox.currentIndex():
            case 0:
                self.color = "limegreen"
            case 1:
                self.color = "magenta"
            case 2:
                self.color = "cyan"
            case 3:
                self.color = "blue"
            case 4:
                self.color = "yellow"
            case 5:
                self.color = "white"
            case _:
                self.color = "#b8cdee"

        self.viewer.setColor(self.color)
        if hasattr(self, 'hidden_window'):
            if self.second_window_toggle.isChecked():
                self.hidden_window.viewer.setColor(self.color)
        self.update_settings()

    def closeEvent(self, event):
        self.mouse_tracker.stop()
        if hasattr(self, 'hidden_window'):
            self.hidden_window.close()
        self.html_server.shutdown()
        self.update_settings_thread()
        self.audio.audio_thread.stop_stream()
        self.midi_listener.terminate()
        self.keyboard_listener.terminate()
        if self.TwitchAPI is not None:
            self.TwitchAPI.terminate()
        event.accept()

    def animateGeometry(self, widget, rect):
        widget.setGeometry(rect)

    def resizeEvent(self, event):
        videoRect = QtCore.QRect(
            QtCore.QPoint(), self.mainFrame.sizeHint().scaled(
                self.size(), QtCore.Qt.AspectRatioMode.IgnoreAspectRatio
            )
        )
        videoRect.moveCenter(self.rect().center())
        self.mainFrame.setGeometry(videoRect)

        self.frame_3.setGeometry(self.get_positions("frame_3", self.hidden_ui))
        self.frame_4.setGeometry(self.get_positions("frame_4", self.hidden_ui))
        self.donationBtnURL.setGeometry(self.get_positions("donationBtnURL", self.hidden_ui))

        if self.editor.isHidden:
            self.editorFrame.setGeometry(self.get_positions("editor", True))
        else:
            self.editorFrame.setGeometry(self.get_positions("editor", self.hidden_ui))

        if hasattr(self, 'hidden_window'):
            if self.second_window_toggle.isChecked():
                self.hidden_window.setGeometry(self.geometry())

        self.update_viewer(self.current_files)

    def moveEvent(self, event):
        if hasattr(self, 'hidden_window'):
            if self.second_window_toggle.isChecked():
                self.hidden_window.setGeometry(self.geometry())

    def get_positions(self, widget, hide=False) -> QtCore.QRect | list[QtCore.QRect]:
        match widget:
            case "donationBtnURL":
                if hide:
                    return QtCore.QRect(int(self.width() / 2)-151, -41, 302, 31)
                else:
                    return QtCore.QRect(int(self.width()/2)-151, 0, 302, 31)
            case "frame_4":
                assetsWidth = self.frame_3.maximumWidth()
                if hide:
                    return QtCore.QRect(-20 - assetsWidth, 10, assetsWidth, self.height() - 20)
                else:
                    return QtCore.QRect(10, 10, assetsWidth, self.height() - 20)
            case "frame_3":
                controlWidth = self.frame_3.maximumWidth()
                if hide:
                    return QtCore.QRect(self.width() + 10, 10, controlWidth, self.height() - 20)
                else:
                    return QtCore.QRect(self.width() - controlWidth - 10, 10, controlWidth, self.height() - 20)
            case "editor":
                editorWidth = self.frame_3.maximumWidth() * 2
                if hide:
                    return QtCore.QRect(self.width() + 10, 10, editorWidth, self.height() - 20)
                else:
                    return QtCore.QRect(self.width() - editorWidth - 10, 10, editorWidth, self.height() - 20)
            case _:
                return QtCore.QRect(0, 0, 100, 100)

    def showColorDialog(self):
        initial = QColor()
        try:
            if "#" in self.color_selector.text():
                raise Exception
            color = [int(i) for i in self.color_selector.text().split(", ")]
            initial.setRed(color[0])
            initial.setGreen(color[1])
            initial.setBlue(color[2])
            initial.setAlpha(color[3])
        except BaseException:
            initial.setRed(0)
            initial.setGreen(0)
            initial.setBlue(0)
            initial.setAlpha(255)

        color = QtWidgets.QColorDialog.getColor(
            initial=initial,
            options=QtWidgets.QColorDialog.ColorDialogOption.ShowAlphaChannel
        )

        if color.isValid():
            color = color.getRgb()
            self.color_selector.setText(", ".join([str(i) for i in color]))
            self.change_color()

    def change_color(self):
        self.colorFrame.setStyleSheet(f"""
        QFrame{{
            background-color: rgba({
                self.color_selector.text() if "#" not in self.color_selector.text() else "0, 0, 0, 255"
            });
            border-bottom-left-radius: 9px;
            border-bottom-right-radius: 5px;
            border-top-left-radius: 9px;
            border-top-right-radius: 5px;
            border-style: outset;
            border-width: 1px;
            border-color: black;
        }}
        """)
        self.update_shadow()

    def hide_shadow(self):
        if self.shadow_toggle.isChecked():
            self.frame_65.show()
        else:
            self.frame_65.hide()
        self.update_shadow()

    def hide_filters(self):
        if self.filters_toggle.isChecked():
            self.frame_67.show()
        else:
            self.frame_67.hide()
        self.update_filters()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    QCoreApplication.setApplicationName("PyNGtuber")

    window = MainWindow()

    window.setWindowIcon(QIcon('icon.ico'))
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
