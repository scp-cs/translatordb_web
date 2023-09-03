# Builtins
from functools import partial
import json
import typing as t

# External
import requests
from cachetools import cached, TTLCache

API_UA = "SCUTTLE Discord service (https://scp-wiki.cz, v1)"
API_URL = "https://discord.com/api"
CDN_URL = "https://cdn.discordapp.com"

class DiscordException(Exception):
    pass

class DiscordClient():

    def __init__(self, auth_token: str) -> None:
        self.auth_token = auth_token
        self.request_headers = {
            "User-Agent": API_UA,
            "Authorization": f"Bot {self.auth_token}",
            "Content-Type": "application/json"
        }    
    
    # TODO: Use uid as cache key
    @cached(TTLCache(maxsize=256, ttl=60 * 60 * 6))
    def _get_user(self, uid: int) -> t.Optional[dict]:
        response = requests.get(API_URL + f'/users/{uid}', headers=self.request_headers)

        user = json.loads(response.content)

        if response.status_code == 200:
            return user
        elif response.status_code == 404:
            return None
        else:
            raise DiscordException("API Request failed")

    def get_global_username(self, uid: int) -> t.Optional[str]:
        try:
            user = self._get_user(uid)
        except DiscordException as e:
            raise e
        if user is None:
            return None
        return user['global_name']

    # TODO: Use uid as cache key
    @cached(TTLCache(maxsize=256, ttl=60 * 60 * 6))
    def get_avatar(self, uid: int, size = 512) -> bytes:
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
            user = self._get_user(uid)
        except DiscordException as e:
            raise e

        if user is None:
            return None

        endpoint = CDN_URL + f"/avatars/{uid}/{user['avatar']}.png"
        response = requests.get(endpoint, headers=self.request_headers, params={'size': str(size)})

        if response.status_code == 200:
            return response.content
        elif response.status_code == 404:
            return None
        else:
            raise DiscordException("CDN Request failed")

    def download_avatars(self, users, path: str) -> None:
        """Downloads the avatars for multiple users

        Args:
            users (List[int]): The User IDs
            path (str): The Download directory
        """
        for u in users:
            if u is None:
                continue
            avatar = self.get_avatar(u)
            if avatar is not None:
                with open(path+f'/{u}.png', 'wb') as file:
                    file.write(avatar)

