from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent, \
    ChannelFollowEvent, ChannelCheerEvent, ChannelRaidEvent, ChannelSubscribeEvent, \
    ChannelSubscriptionGiftEvent
from twitchAPI.chat import Chat, EventData, ChatMessage
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.eventsub.websocket import EventSubWebsocket
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from aiohttp.client_exceptions import ClientConnectionError
from PyQt6 import QtWidgets, QtCore, uic
from PyQt6.QtGui import QIcon
from pynput.keyboard import Listener
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
try:
    import pyautogui
except ValueError:
    pyautogui = None
import os.path
import asyncio
import json
import mido
import time
import os


class TwitchAPI(QThread):
    event_signal = pyqtSignal(dict)
    new_event_signal = pyqtSignal(dict)

    def __init__(self, APP_ID, APP_SECRET, APP_USER, res_dir):
        super().__init__()
        self.APP_ID = APP_ID
        self.APP_SECRET = APP_SECRET
        self.APP_USER = APP_USER
        self.res_dir = res_dir
        self.PUBLIC_APP_ID = "v3pheb41eiqaal8e1pefkjrygpvjt8"
        self.TARGET_SCOPES = [
            AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
            AuthScope.MODERATOR_READ_FOLLOWERS,
            AuthScope.BITS_READ,
            AuthScope.CHANNEL_READ_SUBSCRIPTIONS,
            AuthScope.CHAT_READ
        ]
        self.ignore_commands = False
        self.commands = {}
        self.selected_mode = "toggle"

    def set_selected_mode(self, mode):
        self.selected_mode = mode

    def update_shortcuts(self, commands):
        self.commands = commands

    def request_new_signal(self):
        self.ignore_commands = True

    def resume_normal_operation(self):
        self.ignore_commands = False

    def EventSignalHandler(self, data):
        if self.ignore_commands:
            self.new_event_signal.emit(data)
        else:
            for command in self.commands[data["type"]]:
                emit = False
                match data["type"]:
                    case "TwitchReward":
                        if data["command"]["reward"] == command["command"]["command"]["reward"]:
                            if (data["command"]["prompt"] == command["command"]["command"]["prompt"] or
                                    not command["command"]["command"]["prompt"]):
                                emit = True
                    case "TwitchFollow":
                        emit = True
                    case "TwitchCheer" | "TwitchRaid":
                        if command["command"]["command"][0] <= data["command"] <= command["command"]["command"][1]:
                            emit = True
                    case "TwitchSub" | "TwitchGiftedSub":
                        if data["command"] == command["command"]["command"]:
                            emit = True
                    case "TwitchChatMessage":
                        if data["command"]["parameters"].lower().strip() == "bruh":
                            print(data)

                        if not (
                                command["command"]["command"]["type"] == "Any" or (
                                command["command"]["command"]["type"] == "Mod" and
                                int(data["command"]["tags"].get("mod", 0)) == 1
                                    ) or (
                                command["command"]["command"]["type"] == "VIP" and
                                int(data["command"]["tags"].get("vip", 0)) == 1
                                    ) or (
                                command["command"]["command"]["type"] == "Sub" and
                                int(data["command"]["tags"].get("subscriber", 0)) == 1
                                    )
                        ):
                            return

                        if not (
                                command["command"]["command"]["user"].lower() == data["command"]["tags"]["display-name"].lower() \
                                or not command["command"]["command"]["user"]
                        ):
                            return

                        if command["command"]["command"]["message"]:
                            match command["command"]["command"]["modal"]:
                                case 1:
                                    if command["command"]["command"]["message"] == data["command"]["parameters"].lower().strip():
                                        emit = True
                                case 2:
                                    if command["command"]["command"]["message"] in data["command"]["parameters"].lower().strip():
                                        emit = True
                                case 3:
                                    if data["command"]["parameters"].lower().strip().startswith(
                                            command["command"]["command"]["message"].lower().strip()
                                    ):
                                        emit = True
                                case 4:
                                    if data["command"]["parameters"].lower().strip().endswith(
                                            command["command"]["command"]["message"].lower().strip()
                                    ):
                                        emit = True
                        else:
                            emit = True
                    case _:
                        pass

                if emit:
                    command["source"] = data["type"]
                    self.event_signal.emit(command)

            for key in self.commands:
                for command in self.commands[key]:
                    if data["command"] == command["command"]["command"] and\
                            data["type"] == command["command"]["type"]:
                        command["source"] = data["type"]
                        self.event_signal.emit(command)

    async def on_redeem(self, data: ChannelPointsCustomRewardRedemptionAddEvent):
        self.EventSignalHandler({
            "command": {
                "reward": data.event.reward.title,
                "prompt": data.event.reward.prompt
            },
            "type": "TwitchReward",
            "mode": self.selected_mode
        })

    async def on_follow(self, data: ChannelFollowEvent):
        self.EventSignalHandler(
            {"command": data.event.user_name, "type": "TwitchFollow", "mode": self.selected_mode}
        )

    async def on_cheer(self, data: ChannelCheerEvent):
        self.EventSignalHandler(
            {"command": data.event.bits, "type": "TwitchCheer", "mode": self.selected_mode}
        )

    async def on_raid(self, data: ChannelRaidEvent):
        self.EventSignalHandler(
            {"command": data.event.viewers, "type": "TwitchRaid", "mode": self.selected_mode}
        )

    async def on_sub(self, data: ChannelSubscribeEvent):
        self.EventSignalHandler(
            {"command": data.event.tier, "type": "TwitchSub", "mode": self.selected_mode}
        )

    async def on_gifted_sub(self, data: ChannelSubscriptionGiftEvent):
        self.EventSignalHandler(
            {"command": data.event.tier, "type": "TwitchGiftedSub", "mode": self.selected_mode}
        )

    async def on_message(self, msg: ChatMessage):
        self.EventSignalHandler({"command": msg._parsed, "type": "TwitchChatMessage", "mode": self.selected_mode})

    async def _run(self):
        await self.authorize()
        user = await first(self.twitch.get_users())
        await self.listen(user)

    async def authorize(self):
        try:
            self.twitch = await Twitch(self.APP_ID, self.APP_SECRET)
            helper = UserAuthenticationStorageHelper(
                self.twitch, self.TARGET_SCOPES,
                storage_path=os.path.join(self.res_dir, "Data", "user_token.json")
            )
            await helper.bind()
        except ClientConnectionError:
            pass

    async def on_ready(self, ready_event: EventData):
        print('Bot is ready for work, joining channels')
        await ready_event.chat.join_room(self.APP_USER)

    async def listen(self, user):
        self.eventsub = EventSubWebsocket(self.twitch)
        self.eventsub.start()

        await self.eventsub.listen_channel_points_custom_reward_redemption_add(user.id, callback=self.on_redeem)
        await self.eventsub.listen_channel_follow_v2(user.id, user.id, callback=self.on_follow)
        await self.eventsub.listen_channel_cheer(user.id, callback=self.on_cheer)
        await self.eventsub.listen_channel_raid(to_broadcaster_user_id=user.id,  callback=self.on_raid)
        await self.eventsub.listen_channel_subscribe(user.id, callback=self.on_sub)
        await self.eventsub.listen_channel_subscription_gift(user.id, callback=self.on_gifted_sub)

        if self.APP_USER is not None:
            self.eventChat = await Chat(self.twitch)

            self.eventChat.register_event(ChatEvent.READY, self.on_ready)
            self.eventChat.register_event(ChatEvent.MESSAGE, self.on_message)
            self.eventChat.start()

    async def stop(self):
        await self.eventsub.stop()
        await self.twitch.close()

    def run(self):
        asyncio.run(self._run())


class MidiListener(QThread):
    shortcut = pyqtSignal(dict)
    new_shortcut = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.commands = {}
        self.ignore_commands = False
        self.warning = True
        self.selected_mode = "toggle"

    def set_selected_mode(self, mode):
        self.selected_mode = mode

    def run(self):
        try:
            while True:
                with mido.open_input() as midi_port:
                    for message in midi_port:
                        if self.ignore_commands:
                            self.new_shortcut.emit({"command": message.dict(), "type": "Midi", "mode": self.selected_mode})
                        else:
                            for command in self.commands:
                                if message == command["command"]:
                                    command["source"] = "Midi"
                                    self.shortcut.emit(command)
        except BaseException as err:
            print(f"Midi is not supported on this platform:\n{err}")
            self.warning = False

    def update_shortcuts(self, commands):
        self.commands = commands

    def request_new_signal(self):
        self.ignore_commands = True

    def resume_normal_operation(self):
        self.ignore_commands = False


class KeyboardListener(QThread):
    shortcut = pyqtSignal(dict)
    new_shortcut = pyqtSignal(dict)
    modifier_keys = set()

    def __init__(self):
        super().__init__()
        self.commands = {}
        self.ignore_commands = False
        self.selected_mode = "toggle"

    def set_selected_mode(self, mode):
        self.selected_mode = mode

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
                    self.new_shortcut.emit(
                        {"command": [str(i).replace("'", "") for i in shortcut], "type": "Keyboard", "mode": self.selected_mode}
                    )
                else:
                    for command in self.commands:
                        if [str(i).replace("'", "") for i in shortcut] == command["command"]:
                            command["source"] = "Keyboard"
                            self.shortcut.emit(command)
                    self.modifier_keys = set()
        else:
            self.modifier_keys.discard(key)

    def request_new_signal(self):
        self.ignore_commands = True

    def resume_normal_operation(self):
        self.ignore_commands = False


class MouseTracker(QThread):
    mouse_position = pyqtSignal(dict)

    def __init__(self, target_fps=20):
        super().__init__()
        self.target_fps = target_fps
        self._running = False

    def run(self):
        interval = 1.0 / self.target_fps
        screen_width, screen_height = pyautogui.size()
        center_x, center_y = screen_width // 2, screen_height // 2
        self._running = True
        error_count = 0  # Initialize the error counter
        max_errors = 10  # Set the maximum number of allowed errors

        while self._running:
            start_time = time.time()

            if pyautogui is not None:
                position = pyautogui.position()
                adjusted_position = (position[0] - center_x, position[1] - center_y)
            else:
                adjusted_position = (0, 0)
            try:
                self.mouse_position.emit({
                    "x": adjusted_position[0], "y": adjusted_position[1]
                })
            except AttributeError:
                pass

            elapsed = time.time() - start_time
            if elapsed < interval:
                result = interval - elapsed
                try:
                    time.sleep(result)
                except SystemError:
                    error_count += 1
                    print("Failed to sleep mouse timer, ShortcutsManager.py 344")
                    if error_count >= max_errors:
                        print("Maximum error count reached. Breaking the loop.")
                        adjusted_position = (0, 0)
                        try:
                            self.mouse_position.emit({
                                "x": adjusted_position[0], "y": adjusted_position[1]
                            })
                        except AttributeError:
                            pass
                        break

    def stop(self):
        self._running = False


def find_shortcut_usages(main_folder, current_folder, new_shortcut):
    usages = []
    for root, dirs, files in os.walk(main_folder):
        if root != current_folder:
            for filename in files:
                if filename == "data.json":
                    data_json_path = os.path.join(root, filename)
                    with open(data_json_path, 'r') as json_file:
                        data = json.load(json_file)
                        shortcuts = data.get("shortcuts", None)
                        for shortcut in shortcuts:
                            if shortcut == new_shortcut:
                                usages.append(data_json_path)
    return usages


class ShortcutsDialog(QtWidgets.QDialog):
    new_command = pyqtSignal(dict)

    modes = {
        1: "toggle",
        2: "enable",
        3: "disable",
        4: "timer"
    }

    def __init__(
            self, midi_listener: MidiListener,
            keyboard_listener: KeyboardListener,
            twitch_listener: TwitchAPI,
            data, exe_dir, parent=None
    ):
        super().__init__(parent)
        uic.loadUi(os.path.join(exe_dir, f"UI", "shortcutsManager.ui"), self)

        self.midi_shortcuts = []
        self.keyboard_shortcuts = []
        self.twitch_shortcuts = []

        self.twitchSelector.currentIndexChanged.connect(self.twitchToggle)
        self.modeKeyboard.currentIndexChanged.connect(self.keyboardTimerToggle)
        self.modeMidi.currentIndexChanged.connect(self.midiTimerToggle)
        self.modeTwitch.currentIndexChanged.connect(self.twitchTimerToggle)

        self.twitchToggle()
        self.keyboardTimerToggle()
        self.midiTimerToggle()
        self.twitchTimerToggle()

        self.midi_listener = midi_listener
        self.keyboard_listener = keyboard_listener
        self.twitch_listener = twitch_listener
        self.data = data

        self.setTitle()

        self.midi_listener.request_new_signal()
        self.keyboard_listener.request_new_signal()
        if self.twitch_listener is not None:
            self.twitch_listener.request_new_signal()

        self.midi_listener.new_shortcut.connect(self.handle_midi)
        self.keyboard_listener.new_shortcut.connect(self.handle_keyboard)
        if self.twitch_listener is not None:
            self.twitch_listener.new_event_signal.connect(self.handle_twitch)

        self.setWindowTitle(self.tr("Update Shortcuts"))

        # Connect the signals from both listeners to a slot
        self.midi_listener.shortcut.connect(self.handle_shortcuts)
        self.keyboard_listener.shortcut.connect(self.handle_shortcuts)
        if self.twitch_listener is not None:
            self.twitch_listener.event_signal.connect(self.handle_shortcuts)

        self.saveMidi.clicked.connect(self.save_midi)
        self.savekeyboard.clicked.connect(self.save_keyboard)
        if self.twitch_listener is not None:
            self.saveTwitch.clicked.connect(self.save_twitch)

        self.load_shortcuts()

    def load_shortcuts(self):
        self.keyboard_shortcuts = []
        self.midi_shortcuts = []
        self.twitch_shortcuts = []

        if self.data["value"]["hotkeys"]:
            for shortcut in self.data["value"]["hotkeys"]:
                if shortcut["type"] == "Keyboard":
                    self.keyboard_shortcuts.append(shortcut)
                elif shortcut["type"] == "Midi":
                    self.midi_shortcuts.append(shortcut)
                else:
                    self.twitch_shortcuts.append(shortcut)

        self.show_shortcuts(self.frameKeyboard, self.keyboard_shortcuts)
        self.show_shortcuts(self.frameMidi, self.midi_shortcuts)
        self.show_shortcuts(self.frameTwitch, self.twitch_shortcuts)

    def show_shortcuts(self, frame, data):
        for _ in reversed(range(frame.layout().count())):
            frame.layout().itemAt(_).widget().setParent(None)

        for item in data:
            itemFrame = QtWidgets.QFrame()
            itemFrame.setStyleSheet(
                "* QFrame{background-color: rgba(0, 0, 0, 44);} "
                "* QLabel{background-color: rgba(0, 0, 0, 0);}"
            )
            itemLayout = QtWidgets.QHBoxLayout()
            itemLayout.setContentsMargins(0, 0, 0, 0)

            itemLabel = QtWidgets.QLabel(item["type"])
            itemLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            itemLayout.addWidget(itemLabel)

            commandLabel = QtWidgets.QLabel()
            commandLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            if item["command"] is not None:
                if type(item["command"]) is str:
                    commandLabel.setText(item["command"])
                elif type(item["command"]) is list:
                    commandLabel.setText(", ".join(item["command"]))
                elif type(item["command"]) is dict:
                    values = []
                    for key in item["command"]:
                        values.append(f"{key}: {item['command'][key]}")
                    itemLabel.setText(", ".join(values))
                elif type(item["command"]) is tuple:
                    commandLabel.setText(" - ".join([str(i) for i in item["command"]]))
                else:
                    commandLabel.setText(f'{item["command"]}')
            itemLayout.addWidget(commandLabel)

            modeLabel = QtWidgets.QLabel(f'Mode: {item["mode"].title()}')
            modeLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            itemLayout.addWidget(modeLabel)

            timeLabel = QtWidgets.QLabel()
            timeLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            if "time" in item:
                timeLabel.setText(f'{item["time"]}ms')
            itemLayout.addWidget(timeLabel)

            deleteButton = QtWidgets.QPushButton()
            deleteButton.setIcon(QIcon("Icons/mobile-trash-ui-svgrepo-com.svg"))
            deleteButton.setIconSize(QtCore.QSize(20, 20))
            deleteButton.setSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
            deleteButton.setToolTip("Delete Shortcut")
            deleteButton.clicked.connect(self.delete_shortcut)
            deleteButton.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 255);
            }
            QPushButton:hover {  
                background-color: rgba(255, 0, 0, 100);
            }
            """)
            deleteButton.setAccessibleName(f"{item}")
            itemLayout.addWidget(deleteButton)

            itemFrame.setLayout(itemLayout)
            frame.layout().addWidget(itemFrame)

    def delete_shortcut(self):
        sender = self.sender()

        confirmation = QtWidgets.QMessageBox()
        confirmation.setIcon(QtWidgets.QMessageBox.Icon.Question)
        confirmation.setText("Are you sure you want to delete this shortcut?")
        confirmation.setWindowTitle("Confirmation")
        confirmation.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        result = confirmation.exec()
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            for i, item in enumerate(self.data["value"]["hotkeys"]):
                if eval(sender.accessibleName()) == item:
                    self.data["value"]["hotkeys"].pop(i)
            self.load_shortcuts()

    def setTitle(self):
        if self.data["type"] == "Assets":
            route = self.data["value"]["route"]

            filename = os.path.basename(route)
            parent_folder = os.path.basename(os.path.dirname(route))

            title = f"{filename} {parent_folder}"

            thumbnail_path = os.path.join(
                os.path.dirname(route), "thumbs", os.path.basename(
                    route.replace(".gif", ".png").replace(".webp", ".png")
                )
            )

            self.title.setIcon(QIcon(thumbnail_path))
            self.title.setText(title)
        elif self.data["type"] in ["Avatars", "Expressions"]:
            self.title.setIcon(
                QIcon(f"Models{os.path.sep}{self.data['type']}{os.path.sep}{self.data['name']}{os.path.sep}thumb.png")
            )
            self.title.setText(f"Models{os.path.sep}{self.data['type']}{os.path.sep}{self.data['name']}")
        else:
            self.title.hide()

    def midiTimerToggle(self):
        self.midiTimer.hide()
        if self.modeMidi.currentIndex() == 4:
            self.midiTimer.show()

    def twitchTimerToggle(self):
        self.twitchTimer.hide()
        if self.modeTwitch.currentIndex() == 4:
            self.twitchTimer.show()

    def keyboardTimerToggle(self):
        self.keyboardTimer.hide()
        if self.modeKeyboard.currentIndex() == 4:
            self.keyboardTimer.show()

    def twitchToggle(self):
        match self.twitchSelector.currentIndex():
            case 0:
                self.frameTextTwitch.show()
                self.frameRangeTwitch.hide()
                self.frameTierTwitch.hide()
                self.frameMessageTwitch.hide()
            case 1:
                self.frameTextTwitch.hide()
                self.frameRangeTwitch.hide()
                self.frameTierTwitch.hide()
                self.frameMessageTwitch.hide()
            case 2 | 3:
                self.frameTextTwitch.hide()
                self.frameRangeTwitch.show()
                self.frameTierTwitch.hide()
                self.frameMessageTwitch.hide()
            case 4 | 5:
                self.frameTextTwitch.hide()
                self.frameRangeTwitch.hide()
                self.frameTierTwitch.show()
                self.frameMessageTwitch.hide()
            case 6:
                self.frameTextTwitch.hide()
                self.frameRangeTwitch.hide()
                self.frameTierTwitch.hide()
                self.frameMessageTwitch.show()
            case _:
                self.frameTextTwitch.hide()
                self.frameRangeTwitch.hide()
                self.frameTierTwitch.hide()
                self.frameMessageTwitch.hide()

    @pyqtSlot(dict)
    def handle_keyboard(self, shortcut):
        self.keyboard.setText(", ".join(shortcut["command"]))
        # print(shortcut)

    @pyqtSlot(dict)
    def handle_midi(self, shortcut):
        self.midiType.setCurrentText(f"{shortcut['command']['type']}")
        self.midiTime.setValue(shortcut['command']['time'])
        self.midiNote.setValue(shortcut['command']['note'])
        self.midiVelocity.setValue(shortcut['command']['velocity'])
        self.midiChannel.setValue(shortcut['command']['channel'])
        # print(shortcut)

    @pyqtSlot(dict)
    def handle_twitch(self, shortcut):
        if shortcut["type"] == "TwitchReward":
            self.TwitchReward.setText(str(shortcut["command"]))
        # print(shortcut)

    def save_keyboard(self):
        mode = self.modes.get(self.modeKeyboard.currentIndex(), None)
        command = self.keyboard.text().split(", ")

        missing_data = []
        if command == ['']:
            missing_data.append("Keyboard Shortcut is missing")
        if mode is None:
            missing_data.append("Mode is missing")
        if mode == "timer":
            if self.keyboardTimer.value == 0:
                missing_data.append("Time is missing")
        if missing_data:
            self.missing_data(missing_data)
            return

        shortcut = {
            'command': command,
            'type': 'Keyboard',
            'mode': mode
        }
        if mode == "timer":
            shortcut["time"] = self.keyboardTimer.value()
        self.save_shortcut(shortcut)

    def save_midi(self):
        mode = self.modes.get(self.modeMidi.currentIndex(), None)
        shortcut = {
            "command": {
                "type": self.midiType.currentText(),
                "time": self.midiTime.value(),
                "note": self.midiNote.value(),
                "velocity": self.midiVelocity.value(),
                "channel": self.midiChannel.value()
            },
            'type': 'Midi',
            'mode': mode
        }

        missing_data = []
        if mode is None:
            missing_data.append("Mode")
        if mode == "timer":
            if self.midiTimer.value == 0:
                missing_data.append("Time")
        if missing_data:
            self.missing_data(missing_data)
            return

        if mode == "timer":
            shortcut["time"] = self.midiTimer.value()
        self.save_shortcut(shortcut)

    def missing_data(self, missing: list):
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msg.setText(f"There's problems with the  data to save this shortcut:")
        msg.setInformativeText("\n".join([f"- {i}" for i in missing]))
        msg.setWindowTitle("Problems with Information")
        msg.exec()

    def save_twitch(self):
        types = {
            0: "TwitchReward",
            1: "TwitchFollow",
            2: "TwitchCheer",
            3: "TwitchRaid",
            4: "TwitchSub",
            5: "TwitchGiftedSub",
            6: "TwitchChatMessage"
        }
        index = self.twitchSelector.currentIndex()

        missing_data = []
        match index:
            case 0:
                command = self.TwitchReward.text().strip()
                if not command:
                    missing_data.append("Missing twitch reward")
            case 2 | 3:
                command = (self.TwitchFrom.value(), self.TwitchTo.value())
                if command[0] > command[1]:
                    missing_data.append('The value "To" can\'t be less than the value "From"')
                if command[1] == 0:
                    missing_data.append('The value "To" can\'t be Zero')
            case 4 | 5:
                command = self.TwitchTier.value()
            case 6:
                command = {
                    "message": self.TwitchMessage.text().strip(),
                    "user": self.TwitchUser.text().strip(),
                    "modal": self.TwitchModal.currentIndex(),
                    "type": self.TwitchUserType.currentText()
                }
                if command["modal"] == 0 and command["message"]:
                    missing_data.append("Please, select a match modal")
            case _:
                command = None
        mode = self.modes.get(self.modeTwitch.currentIndex(), None)

        if mode is None:
            missing_data.append("Missing Mode")
        if mode == "timer":
            if self.keyboardTimer.value == 0:
                missing_data.append("Missing Time")

        if missing_data:
            self.missing_data(missing_data)
            return

        shortcut = {
            'command': command,
            'type': types[index],
            'mode': mode
        }
        if mode == "timer":
            shortcut["time"] = self.twitchTimer.value()
        self.save_shortcut(shortcut)

    def save_shortcut(self, shortcut):
        if self.data["type"] in ["Avatars", "Expressions"]:
            mainFolder = os.path.normpath(f"Models/{self.data['type']}")
            used = find_shortcut_usages(mainFolder, self.data['name'], shortcut)
            if used:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                msg.setText(f"This shortcut already exists for another {self.data['type'][:-1].lower()}:")
                msg.setInformativeText(
                    ",".join([
                        i.replace(
                            f"Models{os.path.sep}{self.data['type']}{os.path.sep}", ""
                        ).replace(
                            f"{os.path.sep}data.json", "") for i in used
                    ])
                )
                msg.setWindowTitle("Model Shortcut Exists")
                msg.exec()
                return

        elif self.data["type"] in ["Assets"]:
            if shortcut in self.data["value"]["hotkeys"]:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                msg.setText(f"This shortcut already exists for this {self.data['type'][:-1].lower()}:")
                msg.setInformativeText("Try another one")
                msg.setWindowTitle(f"{self.data['type']} Shortcut Exists")
                msg.exec()
                return

        if shortcut not in self.data["value"]["hotkeys"]:
            self.data["value"]["hotkeys"].append(shortcut)
            self.load_shortcuts()
        else:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            msg.setText(f"This shortcut already exists for this {self.data['type'][:-1].lower()}:")
            msg.setInformativeText("Try another one")
            msg.setWindowTitle(f"{self.data['type']} Shortcut Exists")
            msg.exec()
            return

    @pyqtSlot(dict)
    def handle_shortcuts(self, shortcut):
        self.new_command.emit({"shortcut": shortcut, "data": self.data})
        self.midi_listener.resume_normal_operation()
        self.keyboard_listener.resume_normal_operation()
        self.twitch_listener.resume_normal_operation()
        self.accept()

    def closeEvent(self, event):
        self.new_command.emit(self.data)
        self.midi_listener.new_shortcut.disconnect(self.handle_midi)
        self.keyboard_listener.new_shortcut.disconnect(self.handle_keyboard)
        if self.twitch_listener is not None:
            self.twitch_listener.new_event_signal.disconnect(self.handle_twitch)
        self.midi_listener.resume_normal_operation()
        self.keyboard_listener.resume_normal_operation()
        super().closeEvent(event)
