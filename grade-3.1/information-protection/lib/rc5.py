import struct
from .lcg import lcg
from math import e
import numpy as np


W, R, B = 16, 20, 16
P = int(round((e - 2) * (1 << W))) | 1
Q = int(round(((1 + 5**0.5) / 2 - 1) * (1 << W))) | 1
BLOCK_SIZE = W // 4
mask = (1 << W) - 1
dtype_map = {16: np.uint16, 32: np.uint32}
dtype = dtype_map[W]
packing = "<HH" if W == 16 else "<II"


def rotl(n: int, r: int) -> int:
    r &= W - 1
    return ((n << r) | (n >> (W - r))) & mask


def pad(data: bytes) -> bytes:
    pad_len = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    return data + bytes([pad_len] * pad_len)


def unpad(data: bytes) -> bytes:
    pad_len = data[-1]
    return data[:-pad_len]


def block_to_words(block: bytes):
    return list(struct.unpack(packing, block))


def words_to_block(words):
    return struct.pack(packing, *words)


def rc5_key_expansion(key: bytes):
    # Convert key to words
    C = int(np.ceil(len(key) / (W // 8)))
    L = [0] * C
    for i in range(len(key) - 1, -1, -1):
        L[i // 4] = ((L[i // 4] << 8) | key[i]) & mask

    # Initialize S array
    S = [0] * (2 * R + 2)
    S[0] = P
    for i in range(1, 2 * R + 2):
        S[i] = (S[i - 1] + Q) & mask

    # Mix key into S
    A = B = i = j = 0
    v = 3 * max(C, 2 * R + 2)
    for _ in range(v):
        A = S[i] = rotl((S[i] + A + B) & mask, 3)
        B = L[j] = rotl((L[j] + A + B) & mask, (A + B) & (W - 1))
        i = (i + 1) % len(S)
        j = (j + 1) % C

    return S


def rc5_encrypt_block(plaintext: list, S: list):
    A = (plaintext[0] + S[0]) & mask
    B = (plaintext[1] + S[1]) & mask
    for i in range(1, R + 1):
        A = (rotl(A ^ B, B & (W - 1)) + S[2 * i]) & mask
        B = (rotl(B ^ A, A & (W - 1)) + S[2 * i + 1]) & mask
    return np.array([A, B], dtype=dtype)


def rc5_decrypt_block(ciphertext: tuple[int, int], S: list):
    A, B = ciphertext
    for i in range(R, 0, -1):
        B = rotl((B - S[2 * i + 1]) & mask, W - (A & (W - 1))) ^ A
        A = rotl((A - S[2 * i]) & mask, W - (B & (W - 1))) ^ B
    return np.array([(A - S[0]) & mask, (B - S[1]) & mask], dtype=dtype)


# -----------------------------
#   OPTIMIZED CBC MODE
# -----------------------------
def encrypt_cbc(data: bytes, key: bytes, iv: bytes | None = None) -> bytes:
    """Optimized CBC encryption"""
    data = pad(data)
    S = rc5_key_expansion(key)
    C = int(np.ceil(len(key) / (W // 8)))

    # Generate IV
    bound_lcg = lcg(W, R, B, C)
    if iv is None:
        iv = bytes([next(bound_lcg) & 0xFF for _ in range(BLOCK_SIZE)])

    # Convert to numpy for faster processing
    blocks = np.frombuffer(data, dtype=f"<u{BLOCK_SIZE//2}").reshape(-1, 2).copy()
    iv_block = np.frombuffer(iv, dtype=f"<u{BLOCK_SIZE//2}").reshape(1, 2)[0]

    result_blocks = []
    prev = iv_block.copy()

    for block in blocks:
        # CBC XOR + encryption
        block ^= prev
        encrypted = rc5_encrypt_block(block, S)
        result_blocks.append(encrypted)
        prev = encrypted

    # Convert back to bytes
    result = iv + b"".join(block.tobytes() for block in result_blocks)
    return result


def decrypt_cbc(data: bytes, key: bytes, iv: bytes | None = None) -> bytes:
    """Optimized CBC decryption"""
    S = rc5_key_expansion(key)

    # Extract IV
    if iv is None:
        iv = data[:BLOCK_SIZE]
        data = data[BLOCK_SIZE:]
    else:
        data = data

    # Convert to numpy
    blocks = np.frombuffer(data, dtype=f"<u{BLOCK_SIZE//2}").reshape(-1, 2).copy()
    iv_block = np.frombuffer(iv, dtype=f"<u{BLOCK_SIZE//2}").reshape(1, 2)[0]

    result_blocks = []
    prev = iv_block

    for block in blocks:
        # Decryption + CBC XOR
        decrypted = rc5_decrypt_block(block, S)
        decrypted ^= prev
        result_blocks.append(decrypted)
        prev = block

    # Convert back and unpad
    result = b"".join(block.tobytes() for block in result_blocks)
    return unpad(result)
