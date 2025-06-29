"""
Script used to load articles into the database from a listpages-generated CSV
NOTE: Broken since db moved to peewee
"""

from collections import namedtuple
from datetime import datetime
from typing import List
from msvcrt import getche

from db_legacy import Database
from models.article import Article

dbs = Database()

OriginalArticle = namedtuple('OriginalArticle', 'name author added link')

articles: List[OriginalArticle] = list()

print('Loading CSV...')
with open('czech.csv', 'r', encoding='utf-8') as file:
    lines = file.readlines()
    for line in lines:
        values = line.split(';')
        articles.append(OriginalArticle(values[0], values[1], datetime.strptime(values[2], "%d %b %Y, %H:%M"), values[3]))
    print(f'Processed {len(lines)} lines')

missing = 0
authors = set([a.author for a in articles])
print("Checking author list")
for author in authors:
    author_obj = dbs.get_user_by_wikidot(author.strip())
    if not author_obj:
        print(f'{author:<30s}\t[MISSING]')
        missing+=1
    else:
        print(f'{author:<30s}\t[OK]')
print(f"{missing} / {len(authors)} Authors are missing from database")

for oa in articles:
    author = dbs.get_user_by_wikidot(oa.author)
    if not author:
        print(f'SKIPPING {oa.name} by {oa.author}')
        continue
    new_article = Article(0, oa.name, 0, 0, oa.added, author, None, None, oa.link, True)
    print(f'Add article "{oa.name}" by "{oa.author}"? [Y/N]: ')
    if getche() == b'y':
        dbs.add_article(new_article)
    print()