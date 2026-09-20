"""Password hashing (argon2id)."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain: str) -> str:
    return _HASHER.hash(plain)


def verify_password(plain: str, password_hash: str) -> bool:
    try:
        return _HASHER.verify(password_hash, plain)
    except VerifyMismatchError:
        return False
