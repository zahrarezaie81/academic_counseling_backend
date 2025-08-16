import os
from datetime import datetime, timedelta
from typing import Union, Optional
from dotenv import load_dotenv
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.models import RoleEnum

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(env_path))


ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "narscbjim@$@&^@&%^&RFghgjvbdsha")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", "13ugfdfgh@#$%^@&jkl45678902")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------- Password hashing ------------------

def get_hashed_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ---------------- Token creation ------------------

def create_access_token(subject: Union[str, int], role: RoleEnum, expires_delta: timedelta = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "exp": expire,
        "sub": str(subject),
        "role": role.value
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(subject: Union[str, int], expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    payload = {"exp": expire, "sub": str(subject)}
    return jwt.encode(payload, JWT_REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str, refresh: bool = False) -> Optional[dict]:
    key = JWT_REFRESH_SECRET_KEY if refresh else JWT_SECRET_KEY
    try:
        return jwt.decode(token, key, algorithms=[ALGORITHM])
    except JWTError:
        return None

# ---------------- JWT Dependency ------------------

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=403, detail="Invalid authentication scheme")

        payload = decode_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=403, detail="Invalid or expired token")

        return payload 


# ---------------- Admin Login ------------------

def admin_login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != ADMIN_EMAIL or form_data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    access_token = create_access_token(subject="admin", role=RoleEnum.admin)
    refresh_token = create_refresh_token(subject="admin")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# ---------------- Role Checkers ------------------

def get_current_user(payload: dict = Depends(JWTBearer())) -> dict:
    return payload


def verify_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != RoleEnum.admin.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return True

