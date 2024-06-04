from dataclasses import dataclass
from datetime import datetime

import typing as t

from models.user import User

@dataclass
class Article():
    id: int
    name: str
    words: int
    bonus: int
    added: datetime
    author: User
    corrector: t.Optional[User]
    link: t.Optional[str] = None
    is_original: bool = False