from dataclasses import dataclass
from datetime import datetime
from os import link

import typing as t

from user import User

@dataclass
class Translation():
    id: int
    name: str
    words: int
    bonus: int
    added: datetime
    author: User
    link: t.Optional[str] = None