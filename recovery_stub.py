"""Placeholder recovery helpers for the intent-auth POC."""
from __future__ import annotations

from typing import Iterable


def recover_key(shares: Iterable[bytes]) -> bytes:
    """Naive stand-in for threshold recovery.

    This simply concatenates the shares and truncates to 32 bytes.  Real
    deployments must replace this with a vetted threshold secret sharing
    implementation.
    """

    combined = b"".join(shares)
    return combined[:32]
