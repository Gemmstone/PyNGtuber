import shutil
import time

from Core.ShortcutsManager import MidiListener, KeyboardListener, TwitchAPI, ShortcutsDialog, MouseTracker
from Core.imageGallery import ImageGallery, ExpressionSelector, ModelGallery
from PyQt6.QtCore import QCoreApplication, QEasingCurve, QThreadPool
from PyQt6.QtGui import QIcon, QSyntaxHighlighter, QTextCharFormat, QColor
from Core.audioManager import MicrophoneVolumeWidget
from Core.Viewer import LayeredImageViewer, Worker
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
import json
import copy
import mido
import sys
import os
import re

current_version = "v1.9.0"
repo_owner = "Gemmstone"
repo_name = "PyNGtuber"

directories = ["Data", "Models", "Assets", "Viewer"]
directories_skip = ["Models"]
overwrite_files = ["script.js", "animations.css", "viewer.html"]

os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '4864'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--no-sandbox'

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
if not os.path.isfile(os.path.join(exe_dir, ".gitignore")):
    process = psutil.Process(os.getpid())
    if os.name == 'posix':
        if sys.platform == 'darwin':
            # process.nice(20)
            res_dir = os.path.expanduser("~/Library/Application Support/PyNGtuber")
        else:
            # process.nice(psutil.IOPRIO_HIGH)
            res_dir = os.path.expanduser("~/.config/PyNGtuber")
    elif os.name == 'nt':
        process.nice(psutil.REALTIME_PRIORITY_CLASS)
        res_dir = os.path.join(os.getenv("APPDATA"), "PyNGtuber")

    if not os.path.exists(res_dir):
        os.makedirs(res_dir)

    dest_path = os.path.join(res_dir, "Assets")
    if not os.path.exists(os.path.join(dest_path, "Chereverie")):
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        avatars = [folder for folder in os.listdir(os.path.join(res_dir, "Models", "Avatars")) if "." not in folder]
        expressions = [folder for folder in os.listdir(os.path.join(res_dir, "Models", "Expressions")) if "." not in folder]

        for avatar in avatars:
            file = os.path.join(res_dir, "Models", "Avatars", avatar, "model.json")
            with open(file, "r") as load_file:
                assets = json.load(load_file)
            result = []
            for asset in assets:
                asset = copy.deepcopy(asset)
                if "Chereverie/" not in asset["route"]:
                    asset["route"] = asset["route"].replace("Assets/", "Assets/Chereverie/")
                result.append(asset)
            with open(file, "w") as json_file:
                json.dump(result, json_file, indent=4)

        for expression in expressions:
            file = os.path.join(res_dir, "Models", "Expressions", expression, "model.json")
            with open(file, "r") as load_file:
                assets = json.load(load_file)
            result = []
            for asset in assets:
                asset = copy.deepcopy(asset)
                if "Chereverie/" not in asset["route"]:
                    asset["route"] = asset["route"].replace("Assets/", "Assets/Chereverie/")
                result.append(asset)
            with open(file, "w") as json_file:
                json.dump(result, json_file, indent=4)

        file = os.path.join(res_dir, "Data", "current.json")
        with open(file, "r") as load_file:
            assets = json.load(load_file)
        result = []
        for asset in assets:
            if "Chereverie/" not in asset:
                asset = asset.replace("Assets/", "Assets/Chereverie/")
            result.append(asset)
        with open(file, "w") as json_file:
            json.dump(result, json_file, indent=4)

        file = os.path.join(res_dir, "Data", "parameters.json")
        with open(file, "r") as load_file:
            assets = json.load(load_file)
        result = {}
        for key, value in assets.items():
            if "Chereverie/" not in key:
                result[key.replace("Assets/", "Assets/Chereverie/")] = value
            else:
                result[key] = value
        with open(file, "w") as json_file:
            json.dump(result, json_file, indent=4)

    for directory in directories:
        src_path = os.path.join(exe_dir, directory)
        dest_path = os.path.join(res_dir, directory)

        if not os.path.exists(dest_path):
            shutil.copytree(src_path, dest_path)
        elif directory not in directories_skip:
            update_directory(src_path, dest_path)


class twitchKeysDialog(QtWidgets.QDialog):
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
        if os.path.exists(os.path.join(exe_dir, 'main.exe')):
            self.download_app('Windows')
        elif os.path.exists(os.path.join(exe_dir, 'main.py')):
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
        webbrowser.open(f"https://github.com/{repo_owner}/{repo_name}/releases/tag/{self.data['tag_name']}")

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


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.hidden_ui = False
        uic.loadUi(os.path.join(exe_dir, f"UI", "main.ui"), self)

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

        self.viewer = LayeredImageViewer(exe_dir=res_dir, hw_acceleration=self.settings.get("hardware acceleration", False))
        self.viewer.failed_to_load_images.connect(self.retry_load)
        self.viewer.loadFinishedSignal.connect(self.reboot_audio)
        self.viewer.div_count_signal.connect(self.update_div_count)
        self.viewerFrame.layout().addWidget(self.viewer)
        self.viewer.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.threadpool = QThreadPool()

        self.edited = self.edited = None
        self.color = "limegreen"
        self.viewerFrame_2.setStyleSheet(f"background-color: {self.color}")

        self.setWindowTitle("PyNGTuber")

        self.label_7.setText(
            f'<a href="https://github.com/{repo_owner}/{repo_name}/releases/tag/{current_version}">{current_version}</a>'
        )

        self.color = (184, 205, 238)
        self.file_parameters_current = {}
        self.current_files = []
        self.TwitchAPI = None
        self.json_file = os.path.join(res_dir, "Data", "parameters.json")
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
        self.anim_file_default = os.path.join(exe_dir, "Viewer", "animations.css")
        self.html_file_default = os.path.join(exe_dir, "Viewer", "viewer.html")

        self.selected_animations = {
            0: {
                "animation": self.idle_animation,
                "speed": self.idle_speed,
                "direction": self.idle_animation_direction,
                "pacing": self.idle_animation_pacing,
                "iteration": self.idle_animation_iteration
            },
            1: {
                "animation": self.talking_animation,
                "speed": self.talking_speed,
                "direction": self.talking_animation_direction,
                "pacing": self.talking_animation_pacing,
                "iteration": self.talking_animation_iteration
            },
            2: {
                "animation": self.screaming_animation,
                "speed": self.screaming_speed,
                "direction": self.screaming_animation_direction,
                "pacing": self.screaming_animation_pacing,
                "iteration": self.screaming_animation_iteration
            }
        }

        self.keyboard_listener = KeyboardListener()
        self.keyboard_listener.shortcut.connect(self.shortcut_received)
        self.keyboard_listener.start()
        self.midi_listener = MidiListener()
        self.midi_listener.shortcut.connect(self.shortcut_received)
        self.midi_listener.start()

        try:
            with open(self.json_file, "r") as f:
                self.file_parameters_default = json.load(f)
        except FileNotFoundError:
            pass

        try:
            with open(self.json_file, "r") as f:
                self.file_parameters_current = json.load(f)
        except FileNotFoundError:
            pass

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

        self.file_parameters_default = {os.path.normpath(key): value for key, value in self.file_parameters_default.items()}
        self.file_parameters_current = {os.path.normpath(key): value for key, value in self.file_parameters_current.items()}

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
            engine=self.settings.get('audio engine', "pyaudio")
        )
        self.audio.activeAudio.connect(self.audioStatus)
        self.audioFrame.layout().addWidget(self.audio)
        self.audio.load_settings(settings=self.settings)

        self.idle_animation.activated.connect(self.update_settings)
        self.idle_animation_pacing.activated.connect(self.update_settings)
        self.idle_animation_direction.activated.connect(self.update_settings)
        self.idle_speed.valueChanged.connect(self.update_settings)
        self.idle_animation_iteration.valueChanged.connect(self.update_settings)

        self.talking_animation.activated.connect(self.update_settings)
        self.talking_animation_pacing.activated.connect(self.update_settings)
        self.talking_animation_direction.activated.connect(self.update_settings)
        self.talking_speed.valueChanged.connect(self.update_settings)
        self.talking_animation_iteration.valueChanged.connect(self.update_settings)

        self.screaming_animation.activated.connect(self.update_settings)
        self.screaming_animation_pacing.activated.connect(self.update_settings)
        self.screaming_animation_direction.activated.connect(self.update_settings)
        self.screaming_speed.valueChanged.connect(self.update_settings)
        self.screaming_animation_iteration.valueChanged.connect(self.update_settings)

        self.load_settings()

        self.comboBox.currentIndexChanged.connect(self.update_settings)
        self.PNGmethod.currentIndexChanged.connect(self.update_settings)
        self.HideUI.toggled.connect(self.update_settings)
        self.windowAnimations.toggled.connect(self.update_settings)
        self.flipCanvasToggle.toggled.connect(self.flipCanvas)

        self.track_mouse_x.toggled.connect(self.update_settings)
        self.track_mouse_y.toggled.connect(self.update_settings)
        self.invert_mouse_x.toggled.connect(self.update_settings)
        self.invert_mouse_y.toggled.connect(self.update_settings)

        self.ImageGallery = ImageGallery(
            self.current_files, res_dir=res_dir, exe_dir=exe_dir,
            collection=self.collection.currentText()
        )
        self.ImageGallery.selectionChanged.connect(self.update_viewer)
        self.ImageGallery.currentChanged.connect(self.change_settings_gallery)
        self.scrollArea.setWidget(self.ImageGallery)

        self.comboBox.currentIndexChanged.connect(self.setBGColor)

        self.SettingsGallery = SettingsToolBox(exe_dir=exe_dir, viewer=self.viewer, anim_file=self.anim_file)
        self.SettingsGallery.settings_changed.connect(self.saveSettings)
        self.SettingsGallery.settings_changed_list.connect(self.saveSettings_list)
        self.SettingsGallery.currentChanged.connect(self.being_edited)
        self.SettingsGallery.shortcut.connect(self.dialog_shortcut)
        self.SettingsGallery.delete_shortcut.connect(self.delete_shortcut)
        self.scrollArea_2.setWidget(self.SettingsGallery)

        self.animations_list = []
        self.update_animations(self.settings["animations"])

        self.expressionSelector = ExpressionSelector("Assets")
        self.scrollArea_5.setWidget(self.expressionSelector)

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

        self.setBGColor()
        self.showUI()

        self.PNG.clicked.connect(lambda: self.export_png())

        self.saveAvatar.clicked.connect(self.save_avatar)
        self.saveExpression.clicked.connect(self.save_expression)

        self.createCategory.clicked.connect(self.CreateCategory)
        self.createCollection.clicked.connect(self.CreateCollection)
        self.openFolder.clicked.connect(self.OpenAssetsFolder)
        self.clear.clicked.connect(self.clearSelection)

        self.tabWidget_2.currentChanged.connect(self.changePage)

        self.editorButton.clicked.connect(self.toggle_editor)
        self.closeEditor.clicked.connect(self.toggle_editor)

        self.saveViewerBtn.clicked.connect(self.update_viewer_files)

        self.restoreDefaultsBTN.clicked.connect(self.restore_defaults)

        self.twitchApiBtn.clicked.connect(self.update_keys)

        self.audio_engine.currentIndexChanged.connect(self.change_audio_engine)
        self.collection.currentIndexChanged.connect(self.change_collection)

        self.reference_volume.valueChanged.connect(self.change_max_reference_volume)

        self.generalScale.valueChanged.connect(self.on_zoom_delta_changed)
        self.resetZoom.clicked.connect(lambda: self.generalScale.setValue(100))

        self.mouseTrackingToggle.toggled.connect(self.mouse_tracking_changed)
        self.transparency.toggled.connect(self.being_edited)
        self.performance.toggled.connect(lambda: self.update_viewer(self.current_files, update_gallery=True))

        self.toggle_editor()
        self.change_audio_engine()
        self.being_edited()

        self.mouse_tracker = MouseTracker()
        self.mouse_tracker.mouse_position.connect(self.on_mouse_position_changed)
        self.mouse_tracking_changed()

        self.check_for_update()
        self.update_viewer(self.current_files, update_gallery=True)

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

    def being_edited(self):
        last = copy.deepcopy(self.edited)

        if self.tabWidget_2.currentIndex() == 0 or not self.transparency.isChecked():
            self.edited = None
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

        if last != self.edited:
            QtCore.QTimer.singleShot(500, lambda: self.update_viewer(self.current_files, update_gallery=False))
        self.showUI()

    def check_for_update(self):
        latest_tag, data = self.get_latest_release_tag(repo_owner, repo_name)

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
            self.mouse_tracker.start()
        else:
            self.mouse_tracker.stop()
        self.on_mouse_position_changed({"x": 0, "y": 0})
        self.update_settings()

    def change_audio_engine(self):
        engine_selected = self.audio_engine.currentText()

        if engine_selected == "pyaudio":
            self.label.hide()
            self.reference_volume.hide()
        else:
            self.label.show()
            self.reference_volume.show()

        self.audio.change_audio_engine(engine_selected)
        self.update_settings()

    def on_mouse_position_changed(self, position):
        if self.viewer.is_loaded:
            x = (position['x'] * -1 if self.invert_mouse_x.isChecked() else position['x']) if self.track_mouse_x.isChecked() else 0
            y = (position['y'] * -1 if self.invert_mouse_y.isChecked() else position['y']) if self.track_mouse_y.isChecked() else 0
            self.viewer.page().runJavaScript(f"try{{cursorPosition({x}, {y});}}catch(e){{}}""")

    def on_zoom_delta_changed(self):
        if self.viewer.is_loaded:
            self.viewer.page().runJavaScript(f"document.body.style.zoom = '{self.generalScale.value()}%';""")
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

        self.idle_animation_pacing.setCurrentText(default["idle"].get("pacing", "ease-in-out"))
        self.talking_animation_pacing.setCurrentText(default["talking"].get("pacing", "ease-in-out"))
        self.screaming_animation_pacing.setCurrentText(default.get("screaming", default["talking"]).get("pacing", "ease-in-out"))

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

    def flipCanvas(self):
        self.viewer.page().runJavaScript(f"flip_canvas({180 if self.flipCanvasToggle.isChecked() else 0})")

    def change_max_reference_volume(self):
        self.audio.change_max_reference_volume(new_value=self.reference_volume.value())
        self.update_settings()

    def update_keys(self):
        twitch_dialog = twitchKeysDialog(
            APP_ID=self.twitch_api_client,
            APP_SECRET=self.twitch_api_secret,
            APP_USER=self.twitch_user
        )
        twitch_dialog.new_keys.connect(self.start_twitch_connection)
        twitch_dialog.exec()

    def start_twitch_connection(self, values, starting=False):
        self.twitchApiBtn.setText("Set Twitch API keys")

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
        self.twitchApiBtn.setText("Change Twitch API keys")
        self.TwitchAPI.start()
        self.get_shortcuts()

    def update_viewer_files(self):
        settings_worker = Worker(self.update_settings_thread)
        settings_worker.signals.finished.connect(self.reload_page)
        self.threadpool.start(settings_worker)

    def reload_page(self):
        self.viewer.reload()
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
        self.mouseTrackingToggle.setChecked(self.settings.get("mouse tracking", True))
        self.hw_acceleration.setChecked(self.settings.get("hardware acceleration", True))
        # self.reference_volume.setChecked(self.settings["max_reference_volume"])
        self.track_mouse_x.setChecked(self.settings.get("track_mouse_x", True))
        self.track_mouse_y.setChecked(self.settings.get("track_mouse_y", True))
        self.invert_mouse_x.setChecked(self.settings.get("invert_mouse_x", True))
        self.invert_mouse_y.setChecked(self.settings.get("invert_mouse_y", True))
        self.performance.setChecked(self.settings.get("performance", False))

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
        self.settings = {
            "volume threshold": self.audio.volume.value(),
            "scream threshold": self.audio.volume_scream.value(),
            "delay threshold": self.audio.delay.value(),
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
                    "pacing": self.idle_animation_pacing.currentText(),
                    "direction": self.idle_animation_direction.currentText()
                },
                "talking": {
                    "name": self.talking_animation.currentText(),
                    "speed": self.talking_speed.value(),
                    "iteration": self.talking_animation_iteration.value(),
                    "pacing": self.talking_animation_pacing.currentText(),
                    "direction": self.talking_animation_direction.currentText()
                },
                "screaming": {
                    "name": self.screaming_animation.currentText(),
                    "speed": self.screaming_speed.value(),
                    "iteration": self.screaming_animation_iteration.value(),
                    "pacing": self.screaming_animation_pacing.currentText(),
                    "direction": self.screaming_animation_direction.currentText()
                }
            },
            "audio engine": self.audio_engine.currentText(),
            "mouse tracking": self.mouseTrackingToggle.isChecked(),
            "hardware acceleration": self.hw_acceleration.isChecked(),
            "track_mouse_x": self.track_mouse_x.isChecked(),
            "track_mouse_y": self.track_mouse_y.isChecked(),
            "invert_mouse_x": self.invert_mouse_x.isChecked(),
            "invert_mouse_y": self.invert_mouse_y.isChecked(),
            "performance": self.performance.isChecked(),
            "collection": self.collection.currentText()
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

        for route in self.file_parameters_current:
            if self.file_parameters_current[route]["hotkeys"]:
                for shortcut in self.file_parameters_current[route]["hotkeys"]:
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
                        if (
                                "command" in shortcuts["command"]
                                and command["command"] == shortcuts["command"]["command"]
                                and command["type"] == shortcuts["source"]
                        ) or (
                                (isinstance(shortcuts["command"], str) or isinstance(shortcuts["command"], list))
                                and command["command"] == shortcuts["command"]
                                and command["type"] == shortcuts["source"]
                        ):
                            if command["mode"] in ["toggle", "disable"]:
                                self.current_files.remove(shortcuts["path"])

                            elif command["mode"] == "timer":
                                disable_shortcuts = copy.deepcopy(command)
                                disable_shortcuts["mode"] = "disable"
                                self.shortcut_received(disable_shortcuts)
                                enable_shortcuts = copy.deepcopy(command)
                                enable_shortcuts["mode"] = "enable"
                                QtCore.QTimer.singleShot(command["time"], lambda x=enable_shortcuts: self.shortcut_received(x))
            else:
                if self.file_parameters_default[shortcuts["path"]]:
                    print(shortcuts)
                    for command in self.file_parameters_default[shortcuts["path"]]["hotkeys"]:
                        if (
                                "command" in shortcuts["command"]
                                and command["command"] == shortcuts["command"]["command"]
                                and command["type"] == shortcuts["source"]
                        ) or (
                                (isinstance(shortcuts["command"], str) or isinstance(shortcuts["command"], list))
                                and command["command"] == shortcuts["command"]
                                and command["type"] == shortcuts["source"]
                        ):
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
                if expression in file:
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
        if os.name == "posix":
            subprocess.run(["xdg-open", path])
        elif os.name == "nt":
            subprocess.run(["explorer", path])
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
                    "pacing": self.idle_animation_pacing.currentText(),
                    "direction": self.idle_animation_direction.currentText()
                },
                "talking": {
                    "name": self.talking_animation.currentText(),
                    "speed": self.talking_speed.value(),
                    "iteration": self.talking_animation_iteration.value(),
                    "pacing": self.talking_animation_pacing.currentText(),
                    "direction": self.talking_animation_direction.currentText()
                },
                "screaming": {
                    "name": self.screaming_animation.currentText(),
                    "speed": self.screaming_speed.value(),
                    "iteration": self.screaming_animation_iteration.value(),
                    "pacing": self.screaming_animation_pacing.currentText(),
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

    def audioStatus(self, status=0):
        try:
            if self.viewer.is_loaded:
                animation = self.selected_animations[status]["animation"].currentText()
                speed = self.selected_animations[status]["speed"].value()
                direction = self.selected_animations[status]["direction"].currentText()
                pacing = self.selected_animations[status]["pacing"].currentText()
                iteration = self.selected_animations[status]["iteration"].value()

                self.viewer.page().runJavaScript(
                    f'try{{update_mic({status}, "{animation}", {speed}, "{direction}", "{pacing}", {iteration}, {"true" if self.performance.isChecked() else "false"})}}catch{{}}'
                )
        except AttributeError:
            pass

    def saveSettings_list(self, settings_list):
        for settings in settings_list:
            if settings['default']:
                self.file_parameters_default[settings['value']['route']] = copy.deepcopy(settings["value"])
                self.file_parameters_default[settings['value']['route']].pop("route")
            self.file_parameters_current[settings['value']['route']] = copy.deepcopy(settings["value"])
            self.file_parameters_current[settings['value']['route']].pop("route")
        self.update_viewer(self.current_files)

    def saveSettings(self, settings):
        if settings['default']:
            self.file_parameters_default[settings['value']['route']] = copy.deepcopy(settings["value"])
            self.file_parameters_default[settings['value']['route']].pop("route")
        self.file_parameters_current[settings['value']['route']] = copy.deepcopy(settings["value"])
        self.file_parameters_current[settings['value']['route']].pop("route")
        self.update_viewer(self.current_files)

    def save_parameters_to_json(self):
        with open(self.json_file, "w") as f:
            json.dump(self.file_parameters_default, f, indent=4, ensure_ascii=False)

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
            if i["blinking"] in ["ignore", "blinking_open"] and
               i["talking"] in ["ignore", "talking_closed"]
        ]

        images = []

        if method == 1:
            size_counter = Counter()

            for file_data in files:
                file_route = file_data["route"]
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
                file_route = file_data["route"]
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
            images_list.append({
                "route": os.path.normpath(file),
                **parameters
            })
        return images_list

    def update_viewer(self, files=None, update_gallery=False, update_settings=False):
        images_list = self.getFiles(files)

        if not update_settings:
            self.viewer.updateImages(
                images_list, self.color, self.generalScale.value(), self.edited, self.performance.isChecked()
            )
        if self.tabWidget_2.currentIndex() == 1:
            if self.current_files != files or update_settings:
                self.SettingsGallery.set_items(
                    images_list,
                    self.ImageGallery.itemText(
                        self.ImageGallery.currentIndex()
                    )
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
        self.update_settings()

    def closeEvent(self, event):
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
            QtCore.QPoint(),self.mainFrame.sizeHint().scaled(
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

    def get_positions(self, widget, hide=False) -> QtCore.QRect:
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
