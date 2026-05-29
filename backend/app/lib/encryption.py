from __future__ import annotations

import hmac
import os
from hashlib import sha256

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionConfigError(RuntimeError):
    pass


def _hex_key(name: str) -> bytes:
    value = os.environ.get(name, "").strip()
    if len(value) != 64:
        raise EncryptionConfigError(f"{name} must be a 32-byte key encoded as 64 hex characters.")
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise EncryptionConfigError(f"{name} must be hex encoded.") from exc


def encrypt(value: str | None) -> str | None:
    if value is None:
        return None
    iv = os.urandom(16)
    encrypted = AESGCM(_hex_key("ENCRYPTION_KEY")).encrypt(iv, value.encode("utf-8"), None)
    ciphertext = encrypted[:-16]
    tag = encrypted[-16:]
    return f"{iv.hex()}:{tag.hex()}:{ciphertext.hex()}"


def decrypt(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        iv_hex, tag_hex, ciphertext_hex = value.split(":", 2)
        iv = bytes.fromhex(iv_hex)
        tag = bytes.fromhex(tag_hex)
        ciphertext = bytes.fromhex(ciphertext_hex)
    except ValueError as exc:
        raise EncryptionConfigError("Encrypted values must use iv:authTag:encryptedData hex format.") from exc
    decrypted = AESGCM(_hex_key("ENCRYPTION_KEY")).decrypt(iv, ciphertext + tag, None)
    return decrypted.decode("utf-8")


def hash_for_lookup(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return hmac.new(_hex_key("HASH_KEY"), normalized.encode("utf-8"), sha256).hexdigest()
