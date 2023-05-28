from bcrypt import hashpw, checkpw, gensalt

def pw_hash(pw: str) -> bytes:
    enc = pw.encode('utf-8')
    salt = gensalt()
    return hashpw(enc, salt)

def pw_check(pw1: str, pw2: bytes):
    enc = pw1.encode('utf-8')
    return checkpw(enc, pw2)