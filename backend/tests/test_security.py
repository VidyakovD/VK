import base64
import os

import pytest

from app.core import security


@pytest.fixture(autouse=True)
def _set_test_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        security.settings,
        "token_encryption_key",
        base64.b64encode(os.urandom(32)).decode(),
    )


def test_encrypt_decrypt_roundtrip() -> None:
    plain = "vk1.a.SOME_ACCESS_TOKEN_PAYLOAD"
    encrypted = security.encrypt_token(plain)
    assert encrypted != plain
    assert security.decrypt_token(encrypted) == plain


def test_encrypt_produces_different_ciphertexts() -> None:
    plain = "same-token"
    a = security.encrypt_token(plain)
    b = security.encrypt_token(plain)
    assert a != b  # random nonce → different ciphertext


def test_jwt_roundtrip() -> None:
    token = security.create_access_token(subject="user-123", extra={"vk_id": 42})
    payload = security.decode_token(token, expected_type="access")
    assert payload["sub"] == "user-123"
    assert payload["vk_id"] == 42
    assert payload["type"] == "access"
