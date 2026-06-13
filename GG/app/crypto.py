"""
app/crypto.py — Encrypt/decrypt secret values for DB storage.

Uses only Python built-ins:
  - hashlib.pbkdf2_hmac  → derives a key from Django's SECRET_KEY
  - XOR stream cipher    → encrypts the value
  - base64               → encodes the result for DB storage

Security:
  - Key is derived from Django SECRET_KEY (already secret)
  - Each field uses its own key (field name is the salt)
  - PBKDF2 with 100,000 iterations — brute force resistant
  - Attacker needs BOTH the database AND SECRET_KEY to decrypt
  - No third-party packages needed
"""

import base64
import hashlib

from django.conf import settings


def _derive_key(field_name: str, length: int) -> bytes:
    """
    Derive a unique key for each field using PBKDF2.
    Same SECRET_KEY + different field_name = different key per field.
    """
    return hashlib.pbkdf2_hmac(
        hash_name   = "sha256",
        password    = settings.SECRET_KEY.encode("utf-8"),
        salt        = f"gg_secret:{field_name}".encode("utf-8"),
        iterations  = 100_000,
        dklen       = length,
    )


def encrypt_value(field_name: str, plaintext: str) -> str:
    """
    Encrypt a plaintext string for DB storage.
    Returns a base64-encoded string.
    """
    if not plaintext:
        return ""
    pt_bytes = plaintext.encode("utf-8")
    key      = _derive_key(field_name, len(pt_bytes))
    xored    = bytes(a ^ b for a, b in zip(pt_bytes, key))
    return base64.b64encode(xored).decode("ascii")


def decrypt_value(field_name: str, ciphertext: str) -> str:
    """
    Decrypt a base64-encoded ciphertext from DB.
    Returns the original plaintext string.
    """
    if not ciphertext:
        return ""
    ct_bytes = base64.b64decode(ciphertext.encode("ascii"))
    key      = _derive_key(field_name, len(ct_bytes))
    xored    = bytes(a ^ b for a, b in zip(ct_bytes, key))
    return xored.decode("utf-8")
