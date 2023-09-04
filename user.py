from dataclasses import dataclass
from flask_login import UserMixin

ROLE_NONE = "Žádná"

ROLE_LIMITS = {
    5: 'Překladatel I',
    10: 'Překladatel II',
    25: 'Překladatel III',
    50: 'Překladatel IV',
    100: 'Překladatel V'
}

def get_user_role(points: int) -> str:
    r = ROLE_NONE
    for limit, role in ROLE_LIMITS.items():
        if points < limit:
            break
        r = role
    return r

@dataclass
class User(UserMixin):
    uid: int
    nickname: str
    wikidot: str
    password: bytes
    discord: str
    exempt: bool = False
    temp_pw: bool = False
    display_name: str = None

    def get_id(self) -> int:
        return str(self.uid)
