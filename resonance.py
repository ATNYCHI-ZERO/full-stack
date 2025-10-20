"""Utilities for working with resonance patterns in harmonic datasets."""
from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple


def resonance_match(sequence: Sequence[int | float]) -> List[Tuple[int, int]]:
    """Return index pairs where consecutive elements resonate."""

    pairs = [
        (index, index + 1)
        for index in range(len(sequence) - 1)
        if sequence[index] == sequence[index + 1]
    ]

    if pairs:
        print(f"Resonance matches at index pairs: {pairs}")
    else:
        print("No resonance matches found.")

    return pairs


def detect_resonances(sequences: Iterable[Sequence[int | float]]) -> List[List[Tuple[int, int]]]:
    """Evaluate multiple sequences and return their resonance matches."""

    return [resonance_match(sequence) for sequence in sequences]


__all__ = ["resonance_match", "detect_resonances"]
