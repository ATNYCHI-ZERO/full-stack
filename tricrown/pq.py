"""Minimal wrappers for the post-quantum algorithms required by TRI-CROWN.

The real implementation should delegate to either ``liboqs`` or another
provider that exposes ML-KEM (a.k.a. Kyber), Classic McEliece and ML-DSA.
Here we keep the module importable without external dependencies by providing
clear ``Protocol`` definitions alongside deterministic stubs that are easy to
swap out during integration tests.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Protocol, runtime_checkable


@runtime_checkable
class Encapsulation(Protocol):
    """Protocol for KEM style algorithms."""

    def public_key_bytes(self) -> bytes:  # pragma: no cover - interface definition only
        ...

    def secret_key_bytes(self) -> bytes:  # pragma: no cover - interface definition only
        ...

    def encapsulate(self, peer_public_key: bytes) -> tuple[bytes, bytes]:  # pragma: no cover
        ...

    def decapsulate(self, ciphertext: bytes) -> bytes:  # pragma: no cover
        ...


@dataclass
class StubKEM:
    """Very small deterministic KEM used for documentation-style tests.

    The goal is to make the behaviour predictable so we can write examples
    without pulling in heavyweight PQC bindings.  The shared secret is derived
    from ``sha3_256(pk || ct)`` which of course is *not* secure but keeps the
    interface realistic.
    """

    public_key: bytes
    secret_key: bytes
    name: str
    _decap_cache: Dict[bytes, bytes] = field(default_factory=dict, init=False, repr=False)

    def public_key_bytes(self) -> bytes:
        return self.public_key

    def secret_key_bytes(self) -> bytes:
        return self.secret_key

    def encapsulate(self, peer_public_key: bytes) -> tuple[bytes, bytes]:
        from hashlib import sha3_256

        ct = sha3_256(self.public_key + peer_public_key).digest()
        self._decap_cache[ct] = ct
        return ct, ct

    def decapsulate(self, ciphertext: bytes) -> bytes:
        return self._decap_cache.get(ciphertext, ciphertext)


@dataclass
class StubSignatureKeypair:
    """Stateless hash-based style signature placeholder."""

    secret_key: bytes
    name: str = "ML-DSA-stub"

    def __post_init__(self) -> None:
        from hashlib import sha3_512

        self.public_key = sha3_512(self.secret_key).digest()

    def sign(self, message: bytes) -> bytes:
        from hashlib import sha3_512

        return sha3_512(self.public_key + message).digest()

    @staticmethod
    def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
        from hashlib import sha3_512
        from hmac import compare_digest

        expected = sha3_512(public_key + message).digest()
        return compare_digest(expected, signature)


def random_stub_kem(name: str) -> StubKEM:
    """Generate a random stub KEM instance."""

    pk = os.urandom(64)
    sk = os.urandom(64)
    return StubKEM(public_key=pk, secret_key=sk, name=name)


def random_stub_signature(name: str = "ML-DSA-stub") -> StubSignatureKeypair:
    """Return a deterministic-style signature key pair stub."""

    sk = os.urandom(64)
    return StubSignatureKeypair(secret_key=sk, name=name)
