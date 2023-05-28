from flask import Flask, render_template, redirect, request
from collections import namedtuple
import json

import sqlite3

app = Flask(__name__)

db = {}

User = namedtuple('User', 'nickname discord wikidot articles points role')

def get_users():
    _users = []
    for u in db['users'].items():
        _users.append(User(u[0], u[1]['discord_id'], u[1]['wikidot'], len(u[1]['articles'].keys()), u[1]['total_points'], u[1]['role_level']))
    return sorted(_users, key=lambda u: u.points, reverse=True)

def db_save():
    try:
        with open('translations.json', 'w') as tfile:
            json.dump(db, tfile)
    except IOError as e:
        raise IOError(f"Write error: {str(e)}")

@app.route('/')
def index():
    return render_template('users.j2', users=get_users())

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        return "OK"
    return render_template('login.j2')

if __name__ == '__main__':
    app.config.from_file('config.json', json.load)
    with open('translations_new.json', 'r+') as tfile:
        db = json.load(tfile)
    app.run(debug=True)