from dataclasses import dataclass
from flask_login import UserMixin

ROLE_NONE = "Žádná"

ROLE_LIMITS = {
    5: 'Překladatel I',
    10: 'Překladatel II',
    25: 'Překladatel III',
    50: 'Překladatel IV',
    100: 'Překladatel V',
    200: 'Překladatel VI',
    500: 'Překladatel VII'
}

ROLE_COLORS = {
    5: 'bg-gradient-to-r from-gray-400 to-gray-600',
    10: 'bg-gradient-to-r from-sky-400 to-blue-500',
    25: 'bg-gradient-to-r from-fuchsia-600 to-pink-600',
    50: 'bg-gradient-to-r from-pink-500 via-red-500 to-yellow-500',
    100: 'bg-gradient-to-r from-gray-700 via-gray-900 to-black',
    200: 'bg-gradient-to-r from-slate-900 via-purple-900 to-slate-900',
    500: 'gradient-background'
}

def get_user_role(points: int) -> str:
    r = ROLE_NONE
    for limit, role in ROLE_LIMITS.items():
        if points < limit:
            break
        r = role
    return r

def get_role_color(points: int) -> str:
    r = 'transparent'
    for limit, col in ROLE_COLORS.items():
        if points < limit:
            break
        r = col
    return r

@dataclass
class User(UserMixin):
    uid: int
    nickname: str
    wikidot: str
    password: bytes
    discord: str
    temp_pw: bool = False
    display_name: str = None

    def get_id(self) -> int:
        return str(self.uid)
    
    @property
    def can_login(self) -> bool:
        return self.password != None

    def to_dict(self) -> dict:
        return {
        'id': self.uid,
        'nickname': self.nickname,
        'wikidot': self.wikidot,
        'discord': self.discord,
        'displayName': self.display_name
    }
