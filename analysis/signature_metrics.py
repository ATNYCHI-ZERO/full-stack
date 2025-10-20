"""Numerical helpers for computing summary statistics on signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class SignatureMetrics:
    """Collection of lightweight descriptors for a one-dimensional signal."""

    mean: float
    median: float
    variance: float
    crest_factor: float


def _to_array(signal: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(signal), dtype=float)
    if arr.size == 0:
        raise ValueError("signal must contain at least one element")
    return arr


def compute_signature_metrics(signal: Sequence[float]) -> SignatureMetrics:
    """Return simple descriptive statistics for *signal*."""

    arr = _to_array(signal)
    peak = float(np.max(np.abs(arr)))
    rms = float(np.sqrt(np.mean(np.square(arr))))
    crest = float(peak / (rms + 1e-12))
    return SignatureMetrics(
        mean=float(np.mean(arr)),
        median=float(np.median(arr)),
        variance=float(np.var(arr)),
        crest_factor=crest,
    )


def normalise_signal(signal: Sequence[float]) -> np.ndarray:
    """Return signal scaled to zero mean and unit variance."""

    arr = _to_array(signal)
    arr = arr - np.mean(arr)
    std = np.std(arr)
    if std > 0:
        arr = arr / std
    return arr


__all__ = ["SignatureMetrics", "compute_signature_metrics", "normalise_signal"]
