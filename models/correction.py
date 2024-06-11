from dataclasses import dataclass
from datetime import datetime

from models.article import Article
from models.user import User

@dataclass
class Correction():
    article: Article
    author: User
    corrector: User
    timestamp: datetime
    words: int

    def to_dict(self):
        return {
            'article': self.article.to_dict(),
            'author': self.author.to_dict(),
            'corrector': self.corrector.to_dict(),
            'timestamp': self.timestamp,
            'words': self.words
        }