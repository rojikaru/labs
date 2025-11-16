"""
Collection of all implementations of all labs in the Information Protection course.
"""

from .lcg import lcg, gcd, test_rng, numpy_rng
from .md5 import md5
from .rc5 import encrypt_cbc, decrypt_cbc


__all__ = ["lcg", "gcd", "numpy_rng", "test_rng", "md5", "encrypt_cbc", "decrypt_cbc"]
