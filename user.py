from dataclasses import dataclass
from flask_login import UserMixin

@dataclass
class User(UserMixin):
    uid: int
    nickname: str
    wikidot: str
    discord: str
    password: bytes
    exempt: bool = False

    def get_id(self) -> int:
        return str(self.uid)