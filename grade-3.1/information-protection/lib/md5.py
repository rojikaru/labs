import struct
import numpy as np


BLOCK_SIZE_BYTES = 64  # 512 bits = 64 bytes
SHIFTS = [
    [7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22, 7, 12, 17, 22],
    [5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20, 5, 9, 14, 20],
    [4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23, 4, 11, 16, 23],
    [6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21, 6, 10, 15, 21],
]
UINT32_MASK = 0xFFFFFFFF
SINE_VALUES = [int(np.abs(np.sin(i + 1)) * (2**32)) & UINT32_MASK for i in range(64)]


def leftrotate(number: int, shift: int, wordsize: int = 32) -> int:
    """
    Rotate an integer left by b bits

    :param n: The integer to rotate
    :param b: The number of bits to rotate
    :return: The rotated integer
    """
    mask = (1 << wordsize) - 1
    return ((number << shift) | (number >> (wordsize - shift))) & mask


def md5(message: str | bytes = "") -> str:
    """
    Compute the MD5 hash of a given message.

    :param message: The input message to hash
    :return: The MD5 hash as a hexadecimal string
    """

    # Convert message to bytes
    msg = message.encode("utf-8") if isinstance(message, str) else message
    msg_len_bits = len(msg) * 8

    # Padding: append 1 bit (0x80 byte) followed by zeros, then length
    msg += b"\x80"
    # Pad to 56 bytes mod 64 (leaving 8 bytes for the length)
    while len(msg) % 64 != 56:
        msg += b"\x00"
    msg += struct.pack("<Q", msg_len_bits)

    # Initialize MD5 state (0x0 through 0xF and vice versa)
    a0, b0, c0, d0 = 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476

    # Process each 512-bit chunk
    for chunk_start in range(0, len(msg), BLOCK_SIZE_BYTES):
        chunk = msg[chunk_start : chunk_start + BLOCK_SIZE_BYTES]

        # Break chunk into 16 32-bit little-endian words
        X = list(struct.unpack("<16I", chunk))

        A, B, C, D = a0, b0, c0, d0

        for i in range(64):
            if i < 16:
                F = (B & C) | ((~B) & D)
                g = i
            elif i < 32:
                F = (D & B) | ((~D) & C)
                g = (5 * i + 1) % 16
            elif i < 48:
                F = B ^ C ^ D
                g = (3 * i + 5) % 16
            else:
                F = C ^ (B | (~D))
                g = (7 * i) % 16

            F = (A + F + X[g] + SINE_VALUES[i]) & UINT32_MASK
            A, B, C, D = (
                D,
                (B + leftrotate(F, SHIFTS[i // 16][i % 16])) & UINT32_MASK,
                B,
                C,
            )

        # Add this chunk's hash to result so far
        a0 = (a0 + A) & UINT32_MASK
        b0 = (b0 + B) & UINT32_MASK
        c0 = (c0 + C) & UINT32_MASK
        d0 = (d0 + D) & UINT32_MASK

    # Produce the final hash value (little-endian)
    return struct.pack("<4I", a0, b0, c0, d0).hex()
