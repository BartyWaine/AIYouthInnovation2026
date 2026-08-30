import os
import hmac
import hashlib
import base64
import json
import time
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import SessionLocal
from . import models

SECRET_KEY = os.getenv("JWT_SECRET")
if SECRET_KEY is None:
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("JWT_SECRET environment variable must be set in production.")
    import warnings
    warnings.warn("JWT_SECRET not set — using insecure fallback. Set JWT_SECRET env var in production.")
    SECRET_KEY = "dev-secret-insecure-fallback-only"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return "pbkdf2_sha256$" + salt.hex() + "$" + dk.hex()

def get_password_hash(password: str) -> str:
    return hash_password(password)

def verify_password(password: str, stored: str) -> bool:
    try:
        _method, salt_hex, hash_hex = stored.split("$")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hmac.compare_digest(dk.hex(), hash_hex)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(subject: str, role: str) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    issued = int(time.time())
    payload = {
        "sub": subject,
        "role": role,
        "iat": issued,
        "exp": issued + ACCESS_TOKEN_EXPIRE_SECONDS,
    }
    signing_input = (
        _b64url(json.dumps(header, separators=(",", ":")).encode())
        + "."
        + _b64url(json.dumps(payload, separators=(",", ":")).encode())
    )
    signature = hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + _b64url(signature)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    signing_input = header_b64 + "." + payload_b64
    expected = hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url(expected), sig_b64):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")
    payload = json.loads(_b64url_decode(payload_b64))
    if "exp" in payload and payload["exp"] < int(time.time()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    return payload


def get_current_user(token: str = Depends(oauth2_scheme)) -> models.User:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    db: Session = SessionLocal()
    try:
        user = db.get(models.User, int(user_id))
    finally:
        db.close()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
def require_role(required_role: str):
    def role_dependency(current_user: models.User = Depends(get_current_user)):
        if current_user.role.value != required_role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return role_dependency

