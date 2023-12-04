from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.type import AuthScope
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
import asyncio
import json
import os

apiKeys = os.path.normpath(f"Data{os.path.sep}keys.json")
try:
    with open(apiKeys, "r") as f:
        keys = json.load(f)
        APP_ID = keys["twitch"]["client"]
        APP_SECRET = keys["twitch"]["secret"]
except FileNotFoundError:
    APP_ID = None
    APP_SECRET = None

TARGET_SCOPES = [AuthScope.CHANNEL_MANAGE_REDEMPTIONS]

async def on_redeem(data: ChannelPointsCustomRewardRedemptionAddEvent):
    print(f'{data.event.reward.title} was redeemed!')


async def run():
    twitch = await Twitch(APP_ID, APP_SECRET)
    helper = UserAuthenticationStorageHelper(
        twitch, TARGET_SCOPES,
        storage_path=os.path.normpath(
            f"Data{os.path.sep}user_token.json",

        )
    )
    await helper.bind()

    user = await first(twitch.get_users())

    eventsub = EventSubWebsocket(twitch)
    eventsub.start()

    await eventsub.listen_channel_points_custom_reward_redemption_add(user.id, callback=on_redeem)

    try:
        input('press Enter to shut down...')
    except KeyboardInterrupt:
        pass
    finally:
        await eventsub.stop()
        await twitch.close()


asyncio.run(run())
