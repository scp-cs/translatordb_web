from dataclasses import dataclass
from datetime import datetime

import typing as t

from models.user import User

@dataclass
class Translation():
    id: int
    name: str
    words: int
    bonus: int
    added: datetime
    author: User
    link: t.Optional[str] = None