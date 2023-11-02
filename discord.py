# Builtins
import json
import time
import typing as t
from logging import warning, error, info

# External
import requests

API_UA = "SCUTTLE Discord service (https://scp-wiki.cz, v1)"
API_URL = "https://discord.com/api"
CDN_URL = "https://cdn.discordapp.com"

class DiscordException(Exception):
    pass

class DiscordClient():

    def __new__(*args, **kwargs):
        # Pretend python has static classes and this is one
        raise TypeError("Static class cannot be instantiated")

    @staticmethod
    def _validate_user_id(uid: str):
        if len(uid) not in [18, 19]:
            return False
        try:
            _ = int(uid)
        except Exception:
            return False
        return True

    @staticmethod
    def set_token(auth_token: str):
        DiscordClient.__auth_token = auth_token
        DiscordClient.__request_headers = {
            "User-Agent": API_UA,
            "Authorization": f"Bot {DiscordClient.__auth_token}",
            "Content-Type": "application/json"
        }
    
    @staticmethod
    def _get_user(uid: int) -> t.Optional[dict]:
        response = requests.get(API_URL + f'/users/{uid}', headers=DiscordClient.__request_headers)

        user = json.loads(response.content)

        if response.status_code == 200:
            return user
        elif response.status_code == 404:
            warning(f'Discord user API returned 404 for {uid}')
            return None
        else:
            error(f'Discord API request failed for {uid}')
            raise DiscordException("API Request failed")

    @staticmethod
    def get_global_username(uid: int) -> t.Optional[str]:
        try:
            user = DiscordClient._get_user(uid)
        except DiscordException as e:
            raise e
        if user is None:
            return None
        if user['global_name'] == None:
            return user['username']
        return user['global_name']

    # TODO: Download size 512 pics, scale down to like 64 for front page to save bandwidth and user's CPU
    @staticmethod
    def get_avatar(uid: int, size = 256) -> bytes:
        """Fetches the avatar of a user from Discord's CDN. Results are cached for 6 hours.

        Args:
            uid (int): The user's Discord ID
            size (int): The avatar's size, defaults to 512 px

        Raises:
            DiscordException: Raised when either of the API requests fails

        Returns:
            bytes: A bytes object containing the user's avatar in PNG format
        """
        try:
            user = DiscordClient._get_user(uid)
        except DiscordException as e:
            raise e

        if user is None:
            return None

        endpoint = CDN_URL + f"/avatars/{uid}/{user['avatar']}.png"
        response = requests.get(endpoint, headers=DiscordClient.__request_headers, params={'size': str(size)})

        if response.status_code == 200:
            return response.content
        elif response.status_code == 404:
            warning(f"Discord CDN request returned 404 for {uid}")
            return None
        else:
            error(f"Discord CDN request failed for {uid}")
            raise DiscordException("CDN Request failed")

    @staticmethod
    def download_avatars(users, path: str = './temp/avatar') -> None:
        """Downloads the avatars for multiple users

        Args:
            users (List[int]): The User IDs
            path (str): The Download directory
        """
        for u in users:
            if u is None or not DiscordClient._validate_user_id(u):
                warning(f"Skipping profile update for {u}")
                continue
            avatar = DiscordClient.get_avatar(u)
            if avatar is not None:
                with open(path+f'/{u}.png', 'wb') as file:
                    file.write(avatar)
                time.sleep(0.1) # Wait for a bit so we don't hit the rate limit