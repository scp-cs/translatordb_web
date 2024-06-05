from dataclasses import dataclass
from datetime import datetime

from models.article import Article
from models.user import User

@dataclass
class Correction():
    article: Article
    author: User
    corrector: User