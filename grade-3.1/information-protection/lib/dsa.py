"""
DSA digital signature algorithm implementation using the cryptography library.
Supports key generation, digital signing, and signature verification per DSS standard.
"""

from typing import Tuple, cast
from cryptography.hazmat.primitives.asymmetric import dsa, utils
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend


def generate_dsa_keys(key_size: int = 2048) -> Tuple[dsa.DSAPrivateKey, dsa.DSAPublicKey]:
    """
    Generate DSA key pair.

    Args:
        key_size (int): The size of the key in bits (1024, 2048, 3072, or 4096).
    Returns:
        Tuple[DSAPrivateKey, DSAPublicKey]: The private and public keys.
    """
    private_key = dsa.generate_private_key(key_size=key_size)
    public_key = private_key.public_key()
    return private_key, public_key


def save_private_key(
    private_key: dsa.DSAPrivateKey, password: bytes | None = None
) -> bytes:
    """
    Serialize private key to PEM format.

    Args:
        private_key (DSAPrivateKey): The private key to serialize.
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


def save_public_key(public_key: dsa.DSAPublicKey) -> bytes:
    """
    Serialize public key to PEM format.

    Args:
        public_key (DSAPublicKey): The public key to serialize.
    Returns:
        bytes: The serialized public key in PEM format.
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def load_private_key(
    key_data: bytes, password: bytes | None = None
) -> dsa.DSAPrivateKey:
    """
    Load private key from PEM format.

    Args:
        key_data (bytes): The serialized private key.
        password (bytes | None): Optional password if the key is encrypted.
    Returns:
        DSAPrivateKey: The loaded private key.
    """
    return cast(
        dsa.DSAPrivateKey,
        serialization.load_pem_private_key(
            key_data, password=password, backend=default_backend()
        ),
    )


def load_public_key(key_data: bytes) -> dsa.DSAPublicKey:
    """
    Load public key from PEM format.

    Args:
        key_data (bytes): The serialized public key.
    Returns:
        DSAPublicKey: The loaded public key.
    """
    return cast(
        dsa.DSAPublicKey,
        serialization.load_pem_public_key(key_data, backend=default_backend()),
    )


def sign_data(data: bytes, private_key: dsa.DSAPrivateKey) -> bytes:
    """
    Sign data using DSA private key with SHA-256.

    Args:
        data (bytes): The data to sign.
        private_key (DSAPrivateKey): The DSA private key.
    Returns:
        bytes: The DER-encoded signature.
    """
    return private_key.sign(data, hashes.SHA256())


def sign_data_prehashed(digest: bytes, private_key: dsa.DSAPrivateKey) -> bytes:
    """
    Sign pre-computed hash using DSA private key.

    Used for large files to avoid loading entire file into memory.
    The digest must be computed using SHA-256.

    Args:
        digest (bytes): The pre-computed hash digest.
        private_key (DSAPrivateKey): The DSA private key.
    Returns:
        bytes: The DER-encoded signature.
    """
    return private_key.sign(digest, utils.Prehashed(hashes.SHA256()))


def verify_signature(
    data: bytes, signature: bytes, public_key: dsa.DSAPublicKey
) -> bool:
    """
    Verify DSA signature.

    Args:
        data (bytes): The original data that was signed.
        signature (bytes): The DER-encoded signature to verify.
        public_key (DSAPublicKey): The DSA public key.
    Returns:
        bool: True if signature is valid.
    Raises:
        InvalidSignature: If the signature is invalid.
    """
    public_key.verify(signature, data, hashes.SHA256())
    return True


def verify_signature_prehashed(
    digest: bytes, signature: bytes, public_key: dsa.DSAPublicKey
) -> bool:
    """
    Verify DSA signature using pre-computed hash.

    Used for large files to avoid loading entire file into memory.
    The digest must be computed using SHA-256.

    Args:
        digest (bytes): The pre-computed hash digest.
        signature (bytes): The DER-encoded signature to verify.
        public_key (DSAPublicKey): The DSA public key.
    Returns:
        bool: True if signature is valid.
    Raises:
        InvalidSignature: If the signature is invalid.
    """
    public_key.verify(signature, digest, utils.Prehashed(hashes.SHA256()))
    return True


def signature_to_hex(signature: bytes) -> str:
    """
    Convert DER-encoded signature to hexadecimal string.

    Used for storing signatures in text files as required by the assignment.

    Args:
        signature (bytes): The DER-encoded signature.
    Returns:
        str: The signature as a hexadecimal string.
    """
    return signature.hex()


def signature_from_hex(hex_signature: str) -> bytes:
    """
    Convert hexadecimal string to DER-encoded signature bytes.

    Used for loading signatures from text files as required by the assignment.

    Args:
        hex_signature (str): The signature as a hexadecimal string.
    Returns:
        bytes: The DER-encoded signature.
    """
    return bytes.fromhex(hex_signature)

