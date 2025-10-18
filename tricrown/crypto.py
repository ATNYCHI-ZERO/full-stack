"""Low level cryptographic helpers for the TRI-CROWN 2.0 suite.

This module sticks to well known primitives that are readily available in
``cryptography`` and the Python standard library.  The goal is to centralise
HKDF usage, transcript hashing and the deterministic commitment construction
that powers the record layer.

The actual post-quantum algorithms are provided by :mod:`tricrown.pq`, which
contains lightweight wrappers around liboqs-style bindings.  The wrappers
exposed here only require a ``.encapsulate``/``.decapsulate`` API so that the
high level handshake code can remain agnostic of the specific library chosen
by the integrator.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha3_256, sha3_512
from typing import Iterable

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

SUITE_ID = b"TRICROWN-2.0"


@dataclass(frozen=True)
class HKDFParams:
    """Convenience container for HKDF domain separation parameters."""

    info: bytes
    length: int


def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    """Return ``HKDF-Extract`` using SHA3-512.

    The TRI-CROWN specification uses SHA3-512 everywhere to stay inside the
    NIST post-quantum portfolio.  ``cryptography`` provides a straightforward
    HKDF implementation that we reuse here.
    """

    hkdf = HKDF(
        algorithm=hashes.SHA3_512(),
        length=64,
        salt=salt,
        info=b"TRICROWN extract",
    )
    return hkdf.derive(ikm)


def hkdf_expand(prk: bytes, *, params: HKDFParams) -> bytes:
    """Run ``HKDF-Expand`` with SHA3-512 and explicit domain separation."""

    hkdf = HKDF(
        algorithm=hashes.SHA3_512(),
        length=params.length,
        salt=None,
        info=params.info,
    )
    return hkdf.derive(prk)


def transcript_hash(messages: Iterable[bytes]) -> bytes:
    """Compute the running SHA3-512 transcript hash."""

    h = sha3_512()
    for msg in messages:
        h.update(msg)
    return h.digest()


def commit_tag(
    key_commit: bytes,
    *,
    session_id: bytes,
    sequence: int,
    nonce: bytes,
    aad: bytes,
    ciphertext: bytes,
) -> bytes:
    """Compute the deterministic commitment that authenticates each record."""

    h = sha3_256()
    h.update(key_commit)
    h.update(SUITE_ID)
    h.update(session_id)
    h.update(sequence.to_bytes(8, "big"))
    h.update(nonce)
    h.update(aad)
    h.update(ciphertext)
    return h.digest()


def derive_nonce(chain_key: bytes, *, sequence: int, length: int) -> bytes:
    """Derive a deterministic nonce from the sender chain key."""

    params = HKDFParams(info=b"TRICROWN nonce" + sequence.to_bytes(8, "big"), length=length)
    return hkdf_expand(chain_key, params=params)


def derive_message_key(chain_key: bytes, *, sequence: int) -> tuple[bytes, bytes]:
    """Derive the per-message key and the next chain key."""

    mk_params = HKDFParams(info=b"TRICROWN mk" + sequence.to_bytes(8, "big"), length=32)
    message_key = hkdf_expand(chain_key, params=mk_params)
    next_chain_key = hkdf_extract(b"TRICROWN step", chain_key)
    return message_key, next_chain_key


def mix_shared_secrets(
    *,
    transcript: bytes,
    shared_secrets: Iterable[bytes],
) -> bytes:
    """Combine the raw shared secrets with the transcript hash via HKDF-Extract."""

    combined = b"".join(shared_secrets)
    return hkdf_extract(transcript, combined)
