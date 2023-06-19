from dataclasses import dataclass
from flask_login import UserMixin

@dataclass
class User(UserMixin):
    uid: int
    nickname: str
    wikidot: str
    password: bytes
    discord: str
    exempt: bool = False
    points: float = 0

    def get_id(self) -> int:
        return str(self.uid)