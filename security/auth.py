"""Authentication helpers for the existing OnboardAI SQLite/FastAPI app.
Uses stdlib PBKDF2 password hashing and signed JWT-compatible tokens so the
original backend does not need a new ORM or authentication framework.
"""
import base64
import hashlib
import hmac
import json
import os
from dotenv import load_dotenv

load_dotenv()
import time
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ROLES = {"CUSTOMER", "ANALYST", "QA", "ADMIN"}
ALGORITHM = "HS256"
TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "28800"))
security = HTTPBearer(auto_error=False)


def _secret() -> bytes:
    return os.getenv("AUTH_SECRET", "change-me-in-production-onboardai").encode()


def hash_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return "pbkdf2_sha256$200000$%s$%s" % (
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user: dict[str, Any]) -> str:
    now = int(time.time())
    header = {"alg": ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "customer_id": user.get("customer_id"),
        "iat": now,
        "exp": now + TOKEN_TTL_SECONDS,
    }
    encoded_header = _b64(json.dumps(header, separators=(",", ":")).encode())
    encoded_payload = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{encoded_header}.{encoded_payload}".encode()
    signature = _b64(hmac.new(_secret(), signing_input, hashlib.sha256).digest())
    return f"{encoded_header}.{encoded_payload}.{signature}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature = token.split(".", 2)
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected = _b64(hmac.new(_secret(), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid token signature")
        header = json.loads(_unb64(header_b64))
        payload = json.loads(_unb64(payload_b64))
        if header.get("alg") != ALGORITHM or int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("Token expired")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token") from exc


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentication required")
    from services.auth_service import get_user_by_id
    payload = decode_access_token(credentials.credentials)
    user = get_user_by_id(int(payload["sub"]))
    if not user or not user.get("active"):
        raise HTTPException(status_code=401, detail="User is inactive or no longer exists")
    return user


def require_roles(*roles: str):
    allowed = {role.upper() for role in roles}
    def dependency(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency

def can_access_customer(user: dict, customer_id: int) -> bool:
    return user["role"] in {"ADMIN", "ANALYST", "QA"} or user.get("customer_id") == int(customer_id)


def can_access_case(user: dict, case_id: int) -> bool:
    if user["role"] in {"ADMIN", "ANALYST", "QA"}:
        return True
    from services.case_service import get_case
    case = get_case(case_id)
    return bool(case and user.get("customer_id") == case.get("customer_id"))
