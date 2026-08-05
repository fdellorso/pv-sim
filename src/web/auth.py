"""Single-password session auth via signed HMAC cookie."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

SESSION_COOKIE = "pvsim_session"
_SESSION_TTL_S = 24 * 3600


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64url(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def create_session_token(secret: str) -> str:
    """Return a signed session token (payload.hexdigest)."""
    payload = _b64url(json.dumps({"user": "pvsim", "iat": int(time.time())}).encode())
    digest = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{digest}"


def verify_session_token(secret: str, token: str | None) -> bool:
    """Validate the signed token; also rejects expired tokens."""
    if not token:
        return False
    try:
        payload, digest = token.split(".", 1)
        data = json.loads(_unb64url(payload))
    except (ValueError, json.JSONDecodeError):
        return False

    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, expected):
        return False
    issued_at = data.get("iat", 0)
    return int(time.time()) - issued_at < _SESSION_TTL_S
