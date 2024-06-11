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
    corrector: t.Optional[User] = None
    corrected: datetime = None
    link: t.Optional[str] = None
    is_original: bool = False

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "words": self.words,
            "bonus": self.bonus,
            "added": self.added,
            "author": self.author.to_dict(),
            "corrector": self.corrector.to_dict() if self.corrector else None,
            "corrected": self.corrected,
            "link": self.link
            }