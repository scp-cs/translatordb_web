from flask import Blueprint, send_from_directory
from os import path
from constants import *

UserContent = Blueprint('UserContent', __name__)

@UserContent.route('/content/avatar/<int:uid>')
def get_avatar(uid: int):
    if path.exists(path.join('temp', 'avatar', f'{str(uid)}.png')):        
        return send_from_directory(PROFILE_DIR, f'{str(uid)}.png')
    else:
        return send_from_directory('static', 'discord_default.png')