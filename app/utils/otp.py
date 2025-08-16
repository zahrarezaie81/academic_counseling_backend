import random, string
from datetime import datetime, timedelta

_OTP_EXP_MINUTES = 5
_storage: dict[str, dict] = {}  

def _random_code(k: int = 6) -> str:
    return "".join(random.choices(string.digits, k=k))

def generate_code(email: str) -> str:
    code = _random_code()
    _storage[email] = {
        "code": code,
        "expires": datetime.utcnow() + timedelta(minutes=_OTP_EXP_MINUTES)
    }
    return code

def verify_code(email: str, code: str) -> bool:
    entry = _storage.get(email)
    if not entry:
        return False
    if datetime.utcnow() > entry["expires"]:
        _storage.pop(email, None)
        return False
    if entry["code"] != code:
        return False
    _storage.pop(email, None)
    return True
