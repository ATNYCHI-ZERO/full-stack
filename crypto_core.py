"""Core cryptographic primitives for the intent-auth POC.

This module exposes a minimal key encapsulation stub backed by X25519 along
with symmetric encryption helpers built on AES-GCM.  The goal is to keep the
interfaces close to what a production KEM + AEAD stack would provide so that
real PQC libraries can be swapped in later.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def _serialize_public_key(pub: X25519PublicKey) -> bytes:
    """Serialize an X25519 public key to raw bytes."""
    return pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def _deserialize_public_key(data: bytes) -> X25519PublicKey:
    """Rebuild an X25519 public key from raw bytes."""
    return X25519PublicKey.from_public_bytes(data)


class KEMStub:
    """Simplified KEM using X25519 for portability.

    The interface mirrors that of a real post-quantum KEM where `encapsulate`
    returns both the encapsulated key material that is sent with the ciphertext
    and the derived shared secret.  Consumers should treat this as a drop-in
    seam for a production KEM (e.g., Kyber).
    """

    @staticmethod
    def encapsulate(peer_public: X25519PublicKey) -> Tuple[bytes, bytes]:
        """Generate an ephemeral key and shared secret for the recipient.

        Returns a tuple of (encapsulated_bytes, shared_secret).
        """

        eph_sk = X25519PrivateKey.generate()
        eph_pk = eph_sk.public_key()
        shared = eph_sk.exchange(peer_public)
        return _serialize_public_key(eph_pk), shared

    @staticmethod
    def decapsulate(private_key: X25519PrivateKey, encapsulated: bytes) -> bytes:
        """Recover the shared secret using the recipient's private key."""

        peer_public = _deserialize_public_key(encapsulated)
        return private_key.exchange(peer_public)


@dataclass
class CipherPackage:
    """Container for ciphertext artifacts returned by :func:`encrypt_message`."""

    ciphertext: bytes
    nonce: bytes


def derive_key(shared_secret: bytes, operator_fingerprint: bytes) -> bytes:
    """Derive a symmetric key from the shared secret and operator fingerprint."""

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=operator_fingerprint,
        info=b"intent-auth-envelope",
    )
    return hkdf.derive(shared_secret)


def encrypt_message(plaintext: bytes, key: bytes, *, associated_data: bytes | None = None) -> CipherPackage:
    """Encrypt *plaintext* with AES-GCM returning the ciphertext package."""

    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return CipherPackage(ciphertext=ciphertext, nonce=nonce)


def decrypt_message(ciphertext: bytes, nonce: bytes, key: bytes, *, associated_data: bytes | None = None) -> bytes:
    """Decrypt AES-GCM ciphertext returning the original plaintext."""

    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, associated_data)
