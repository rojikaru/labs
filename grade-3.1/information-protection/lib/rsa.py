"""
RSA encryption algorithm implementation using the cryptography library.
Supports key generation, file encryption/decryption in hybrid and chunked modes.
"""

from typing import Literal, Tuple, cast
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
import struct


EncryptionMode = Literal["hybrid", "chunked"]


def generate_rsa_keys(
    key_size: int = 2048,
) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """
    Generate RSA key pair.

    Args:
        key_size (int): The size of the key in bits (1024, 2048, or 4096).
    Returns:
        Tuple[RSAPrivateKey, RSAPublicKey]: The private and public keys.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=key_size, backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


def save_private_key(
    private_key: rsa.RSAPrivateKey, password: bytes | None = None
) -> bytes:
    """
    Serialize private key to PEM format.

    Args:
        private_key (RSAPrivateKey): The private key to serialize.
        password (bytes | None): Optional password to encrypt the key.
    Returns:
        bytes: The serialized private key in PEM format.
    """
    encryption = (
        serialization.BestAvailableEncryption(password)
        if password
        else serialization.NoEncryption()
    )

    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )


def save_public_key(public_key: rsa.RSAPublicKey) -> bytes:
    """
    Serialize public key to PEM format.

    Args:
        public_key (RSAPublicKey): The public key to serialize.
    Returns:
        bytes: The serialized public key in PEM format.
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def load_private_key(
    key_data: bytes, password: bytes | None = None
) -> rsa.RSAPrivateKey:
    """
    Load private key from PEM format.

    Args:
        key_data (bytes): The serialized private key.
        password (bytes | None): Optional password if the key is encrypted.
    Returns:
        RSAPrivateKey: The loaded private key.
    """
    return cast(
        rsa.RSAPrivateKey,
        serialization.load_pem_private_key(
            key_data, password=password, backend=default_backend()
        ),
    )


def load_public_key(key_data: bytes) -> rsa.RSAPublicKey:
    """
    Load public key from PEM format.

    Args:
        key_data (bytes): The serialized public key.
    Returns:
        RSAPublicKey: The loaded public key.
    """
    return cast(
        rsa.RSAPublicKey,
        serialization.load_pem_public_key(key_data, backend=default_backend()),
    )


# -----------------------------
#      HYBRID MODE (RSA + AES)
# -----------------------------


def rsa_encrypt_hybrid(data: bytes, public_key: rsa.RSAPublicKey) -> bytes:
    """
    Encrypt data using hybrid encryption (RSA + AES).
    RSA encrypts the AES key, AES encrypts the data.

    Args:
        data (bytes): The data to encrypt.
        public_key (RSAPublicKey): The RSA public key.
    Returns:
        bytes: The encrypted data with format [aes_key_len][encrypted_aes_key][iv][encrypted_data].
    """
    # Generate random AES-256 key and IV
    aes_key = os.urandom(32)  # 256 bits
    iv = os.urandom(16)  # 128 bits for AES

    # Encrypt data with AES-256-CBC
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Add PKCS7 padding
    padding_length = 16 - (len(data) % 16)
    padded_data = data + bytes([padding_length] * padding_length)

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    # Encrypt AES key with RSA
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # Pack: [encrypted_aes_key_length (4 bytes)][encrypted_aes_key][iv][encrypted_data]
    result = struct.pack("<I", len(encrypted_aes_key))
    result += encrypted_aes_key
    result += iv
    result += encrypted_data

    return result


def rsa_decrypt_hybrid(encrypted_data: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
    """
    Decrypt data encrypted with hybrid encryption (RSA + AES).

    Args:
        encrypted_data (bytes): The encrypted data.
        private_key (RSAPrivateKey): The RSA private key.
    Returns:
        bytes: The decrypted data.
    """
    # Unpack: [encrypted_aes_key_length][encrypted_aes_key][iv][encrypted_data]
    aes_key_length = struct.unpack("<I", encrypted_data[:4])[0]
    offset = 4

    encrypted_aes_key = encrypted_data[offset : offset + aes_key_length]
    offset += aes_key_length

    iv = encrypted_data[offset : offset + 16]
    offset += 16

    encrypted_file_data = encrypted_data[offset:]

    # Decrypt AES key with RSA
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # Decrypt data with AES
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_file_data) + decryptor.finalize()

    # Remove PKCS7 padding
    padding_length = decrypted_data[-1]
    return decrypted_data[:-padding_length]


# -----------------------------
#      CHUNKED MODE (Pure RSA)
# -----------------------------


def rsa_encrypt_chunked(data: bytes, public_key: rsa.RSAPublicKey) -> bytes:
    """
    Encrypt data using pure RSA in chunks.

    Args:
        data (bytes): The data to encrypt.
        public_key (RSAPublicKey): The RSA public key.
    Returns:
        bytes: The encrypted data as concatenated encrypted chunks.
    """
    key_size = public_key.key_size // 8  # Key size in bytes
    # OAEP padding overhead is 2 * hash_length + 2 (SHA-256 = 32 bytes, so 66 bytes overhead)
    max_chunk_size = key_size - 2 * 32 - 2  # 66 bytes overhead for OAEP with SHA-256

    result = b""

    for i in range(0, len(data), max_chunk_size):
        chunk = data[i : i + max_chunk_size]
        encrypted_chunk = public_key.encrypt(
            chunk,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        result += encrypted_chunk

    return result


def rsa_decrypt_chunked(encrypted_data: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
    """
    Decrypt data encrypted with pure RSA in chunks.

    Args:
        encrypted_data (bytes): The encrypted data.
        private_key (RSAPrivateKey): The RSA private key.
    Returns:
        bytes: The decrypted data.
    """
    key_size = private_key.key_size // 8  # Key size in bytes
    chunk_size = key_size  # Each encrypted chunk is exactly key_size bytes

    result = b""

    for i in range(0, len(encrypted_data), chunk_size):
        encrypted_chunk = encrypted_data[i : i + chunk_size]
        decrypted_chunk = private_key.decrypt(
            encrypted_chunk,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        result += decrypted_chunk

    return result


# -----------------------------
#      UNIFIED INTERFACE
# -----------------------------


def rsa_encrypt_file(
    data: bytes, public_key: rsa.RSAPublicKey, mode: EncryptionMode = "hybrid"
) -> bytes:
    """
    Encrypt file data using RSA.

    Args:
        data (bytes): The data to encrypt.
        public_key (RSAPublicKey): The RSA public key.
        mode (EncryptionMode): The encryption mode ("hybrid" or "chunked").
    Returns:
        bytes: The encrypted data.
    """
    if mode == "chunked":
        return rsa_encrypt_chunked(data, public_key)
    else:
        return rsa_encrypt_hybrid(data, public_key)


def rsa_decrypt_file(
    encrypted_data: bytes,
    private_key: rsa.RSAPrivateKey,
    mode: EncryptionMode = "hybrid",
) -> bytes:
    """
    Decrypt file data encrypted with RSA.

    Args:
        encrypted_data (bytes): The encrypted data.
        private_key (RSAPrivateKey): The RSA private key.
        mode (EncryptionMode): The encryption mode ("hybrid" or "chunked").
    Returns:
        bytes: The decrypted data.
    """
    if mode == "chunked":
        return rsa_decrypt_chunked(encrypted_data, private_key)
    else:
        return rsa_decrypt_hybrid(encrypted_data, private_key)
