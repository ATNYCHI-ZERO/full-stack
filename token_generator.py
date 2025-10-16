"""Utility functions for generating deterministic residue-based tokens."""

from __future__ import annotations

import hashlib
from typing import Iterable, Tuple


# MODS is a list of integers used as the initial moduli for the
# ``door_walk_residue`` function.  The ``get_token`` function will generate one
# residue for each number in this list.
MODS: Tuple[int, ...] = (2, 3, 5, 7, 11, 13, 17, 19)


def sha256_int(s: str) -> int:
    """Compute the SHA-256 hash of ``s`` and return it as an integer."""

    h = hashlib.sha256(s.encode("utf-8")).digest()
    return int.from_bytes(h, "big")


def door_walk_residue(N: int, m: int, direction: str = "forward") -> int:
    """Calculate a non-zero residue for ``N`` starting from modulus ``m``.

    The function starts by computing ``N % m``.  If the result is non-zero,
    that residue is returned.  Otherwise we "walk" to the next modulus (either
    incrementing or decrementing depending on the ``direction`` argument) until
    a non-zero residue is found.  Moduli smaller than 2 are normalised to 2.
    """

    current_m = m
    while True:
        # Ensure the modulus is at least 2.
        if current_m < 2:
            current_m = 2

        r = N % current_m
        if r != 0:
            return r

        # Move to the next modulus
        if direction == "forward":
            current_m += 1
        else:
            current_m -= 1


def get_token(word: str, moduli: Iterable[int] = MODS) -> Tuple[int, ...]:
    """Generate a tuple of residues for ``word`` using ``moduli``.

    The hash of ``word`` is computed using :func:`sha256_int`, and for each
    modulus in ``moduli`` we compute a residue using
    :func:`door_walk_residue`.  Each residue is guaranteed to be non-zero.
    """

    N = sha256_int(word)
    return tuple(door_walk_residue(N, m) for m in moduli)


if __name__ == "__main__":
    example = "22129288"
    print(f"The token for '{example}' is: {get_token(example)}")
