import json
from datetime import datetime

with open('translations.json', 'r') as jfile:
    db = json.load(jfile)

_newdb = {"lastupdate": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "users": db}

with open("translations_new.json", 'wt') as tnew:
    json.dump(_newdb, tnew)