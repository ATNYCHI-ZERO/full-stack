"""Utility functions for working with modular arithmetic."""
from __future__ import annotations

from typing import Literal


Direction = Literal["forward", "backward"]


def door_walk_residue(N: int, m: int, direction: Direction = "forward") -> int:
    """Find the first non-zero remainder of ``N`` while walking the modulus.

    Starting at ``m`` the function repeatedly adjusts the modulus by ``1`` in
    the requested ``direction`` (either ``"forward"`` or ``"backward"``) until
    a non-zero remainder is produced. The resulting remainder is returned using
    Python's modulo semantics which means that the sign of the remainder follows
    the sign of the modulus.

    Args:
        N: The dividend whose remainder should be computed.
        m: The starting modulus.
        direction: ``"forward"`` to increment the modulus or ``"backward"`` to
            decrement the modulus on each step.

    Returns:
        The first non-zero remainder encountered while scanning the moduli.

    Raises:
        TypeError: If ``N``, ``m`` or ``direction`` have incorrect types.
        ValueError: If ``direction`` is invalid or ``N`` is zero meaning that no
            non-zero remainder exists.
    """

    if not isinstance(N, int) or not isinstance(m, int):
        raise TypeError("N and m must be integers.")

    if not isinstance(direction, str):
        raise TypeError("direction must be a string.")

    normalized_direction = direction.lower()
    if normalized_direction not in ("forward", "backward"):
        raise ValueError("direction must be either 'forward' or 'backward'.")

    if N == 0:
        raise ValueError("N must be non-zero to produce a non-zero remainder.")

    step = 1 if normalized_direction == "forward" else -1
    current_m = m

    while True:
        if current_m == 0:
            current_m += step
            continue

        remainder = N % current_m
        if remainder != 0:
            return remainder

        current_m += step
