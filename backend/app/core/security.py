import base64
import hashlib
import hmac
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qsl, urlencode

import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


# ----------------------------------------------------------------------------
# JWT
# ----------------------------------------------------------------------------
def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": _now(),
        "exp": _now() + timedelta(seconds=settings.jwt_access_ttl_seconds),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(subject: str) -> str:
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": _now(),
        "exp": _now() + timedelta(seconds=settings.jwt_refresh_ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Expected token type '{expected_type}'")
    return payload


# ----------------------------------------------------------------------------
# VK launch_params signature validation
# https://dev.vk.com/mini-apps/auth
# ----------------------------------------------------------------------------
def validate_vk_launch_params(query_string: str) -> dict[str, str] | None:
    """
    Validates the signature of VK Mini App launch params.

    Args:
        query_string: raw query string from launch URL, e.g.
            "vk_user_id=1&vk_app_id=123&...&sign=<base64url>"

    Returns:
        Parsed params dict if signature is valid, else None.
    """
    if not settings.vk_app_secure_key:
        # Dev mode without registered VK app — accept everything.
        # MUST be rejected in production via settings check at startup.
        return dict(parse_qsl(query_string))

    params = dict(parse_qsl(query_string))
    sign = params.pop("sign", None)
    if not sign:
        return None

    vk_params = {k: v for k, v in params.items() if k.startswith("vk_")}
    if not vk_params:
        return None

    ordered = urlencode(sorted(vk_params.items()))
    expected = (
        base64.urlsafe_b64encode(
            hmac.new(
                settings.vk_app_secure_key.encode(),
                ordered.encode(),
                hashlib.sha256,
            ).digest()
        )
        .decode()
        .rstrip("=")
    )

    if not hmac.compare_digest(expected, sign):
        return None

    return params


# ----------------------------------------------------------------------------
# AES-256-GCM for VK community access tokens at rest
# ----------------------------------------------------------------------------
def _get_aes_key() -> bytes:
    key = settings.token_encryption_key
    try:
        decoded = base64.b64decode(key)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("TOKEN_ENCRYPTION_KEY must be base64-encoded") from exc
    if len(decoded) != 32:
        raise ValueError("TOKEN_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return decoded


def encrypt_token(plaintext: str) -> str:
    aes = AESGCM(_get_aes_key())
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ct).decode()


def decrypt_token(ciphertext_b64: str) -> str:
    aes = AESGCM(_get_aes_key())
    raw = base64.b64decode(ciphertext_b64)
    nonce, ct = raw[:12], raw[12:]
    return aes.decrypt(nonce, ct, None).decode()
