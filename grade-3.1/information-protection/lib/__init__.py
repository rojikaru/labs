"""
Collection of all implementations of all labs in the Information Protection course.
"""

from .lcg import lcg, gcd, test_rng, numpy_rng
from .md5 import md5
from .rc5 import encrypt_cbc, decrypt_cbc
from .rsa import (
    generate_rsa_keys,
    save_private_key,
    save_public_key,
    load_private_key,
    load_public_key,
    rsa_encrypt_file,
    rsa_decrypt_file,
)


__all__ = [
    "lcg",
    "gcd",
    "numpy_rng",
    "test_rng",
    "md5",
    "encrypt_cbc",
    "decrypt_cbc",
    "generate_rsa_keys",
    "save_private_key",
    "save_public_key",
    "load_private_key",
    "load_public_key",
    "rsa_encrypt_file",
    "rsa_decrypt_file",
]
