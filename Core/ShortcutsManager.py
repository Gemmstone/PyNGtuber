from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent, \
    ChannelFollowEvent, ChannelCheerEvent, ChannelRaidEvent, ChannelSubscribeEvent, \
    ChannelSubscriptionGiftEvent
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.eventsub.websocket import EventSubWebsocket
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from twitchAPI.type import AuthScope
from pynput.keyboard import Listener
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
import asyncio
import mido
import os


class TwitchAPI(QThread):
    event_signal = pyqtSignal(dict)
    new_event_signal = pyqtSignal(dict)

    def __init__(self, APP_ID, APP_SECRET):
        super().__init__()
        self.APP_ID = APP_ID
        self.APP_SECRET = APP_SECRET
        self.TARGET_SCOPES = [
            AuthScope.CHANNEL_MANAGE_REDEMPTIONS,
            AuthScope.MODERATOR_READ_FOLLOWERS,
            AuthScope.BITS_READ,
            AuthScope.CHANNEL_READ_SUBSCRIPTIONS
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
            for key in self.commands:
                for command in self.commands[key]:
                    if data["command"] == command["command"]["command"] and\
                            data["type"] == command["command"]["type"]:
                        command["source"] = data["type"]
                        self.event_signal.emit(command)

    async def on_redeem(self, data: ChannelPointsCustomRewardRedemptionAddEvent):
        self.EventSignalHandler(
            {"command": data.event.reward.title, "type": "TwitchReward", "mode": self.selected_mode}
        )

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

    async def _run(self):
        self.twitch = await Twitch(self.APP_ID, self.APP_SECRET)
        helper = UserAuthenticationStorageHelper(
            self.twitch, self.TARGET_SCOPES,
            storage_path=os.path.normpath(
                f"Data{os.path.sep}user_token.json",
            )
        )
        await helper.bind()

        user = await first(self.twitch.get_users())

        self.eventsub = EventSubWebsocket(self.twitch)
        self.eventsub.start()

        await self.eventsub.listen_channel_points_custom_reward_redemption_add(user.id, callback=self.on_redeem)
        await self.eventsub.listen_channel_follow_v2(user.id, user.id, callback=self.on_follow)
        await self.eventsub.listen_channel_cheer(user.id, callback=self.on_cheer)
        await self.eventsub.listen_channel_raid(to_broadcaster_user_id=user.id,  callback=self.on_raid)
        await self.eventsub.listen_channel_subscribe(user.id, callback=self.on_sub)
        await self.eventsub.listen_channel_subscription_gift(user.id, callback=self.on_gifted_sub)

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
                        elif message.type == 'note_on':
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