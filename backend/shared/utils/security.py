import secrets
from typing import Tuple

import bcrypt

PASSWORD_MIN_LENGTH = 8


def hash_password(raw_password: str) -> str:
    password_bytes = raw_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(raw_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(raw_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def validate_password_policy(raw_password: str) -> Tuple[bool, str]:
    if len(raw_password) < PASSWORD_MIN_LENGTH:
        return False, "パスワードは8文字以上にしてください。"
    if not any(c.isalpha() for c in raw_password) or not any(c.isdigit() for c in raw_password):
        return False, "パスワードは英字と数字を含めてください。"
    return True, ""


def generate_token(length: int = 32) -> str:
    # urlsafeで招待トークンを生成。長さ64文字程度になる
    return secrets.token_urlsafe(length)
