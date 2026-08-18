import hashlib
import os


def hash_password(plain_password: str) -> str:
    salt = os.urandom(16).hex()
    digest = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    check = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
    return check == digest