from connectors.discord import DiscordClient, DiscordException
from extensions import dbs
from PIL import Image
from io import BytesIO
from logging import warning
from os.path import join
import time

def update_nicknames_task():
    users = dbs.users()
    for user in users:
        if not user.discord:
            warning(f"Skipping nickname update for {user.nickname}")
            continue
        try:
            new_nickname = DiscordClient.get_global_username(user.discord)
        except DiscordException:
            warning(f"Skipping nickname update for {user.nickname} (API error)")
            continue
        if new_nickname != None:
            user.display_name = new_nickname
            dbs.update_user(user)
        time.sleep(0.2) # Wait a bit so the API doesn't 429

def download_avatars_task(path: str = './temp/avatar', override_ids = None):
    ids = override_ids or [user.discord for user in dbs.users()]
    for user in ids:
        if user is None or not DiscordClient._validate_user_id(user):
            warning(f"Skipping profile update for {user} (Empty or invalid Discord ID)")
            continue
        avatar = DiscordClient.get_avatar(user)
        if avatar is not None:
            with open(join(path,f'{user}.png'), 'wb') as file:
                file.write(avatar)
                Image.open(BytesIO(avatar)).resize((64, 64), Image.Resampling.NEAREST).save(join(path,f'{user}_thumb.png')) # Create a 64x64 thumnail and save it as [ID]_thumb.png

            time.sleep(0.1) # Wait for a bit so we don't hit the rate limit