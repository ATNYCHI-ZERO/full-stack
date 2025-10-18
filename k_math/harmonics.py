"""Utilities for building K-Math harmonic detox waveforms.

This module treats the harmonic detox process as a structured signal
composition problem.  Each harmonic band carries a resonance intent and
is mixed into a unified waveform that can be exported as PCM audio for
use with PEMF, tone generators, or neurofeedback devices.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np


@dataclass(frozen=True)
class HarmonicBand:
    """Single sinusoidal component inside a therapeutic stack."""

    name: str
    frequency_hz: float
    amplitude: float
    phase: float = 0.0

    def sample(self, t: np.ndarray) -> np.ndarray:
        """Return the waveform contribution for the provided timeline."""
        return self.amplitude * np.sin(2 * np.pi * self.frequency_hz * t + self.phase)


@dataclass
class HarmonicProgram:
    """Full waveform program composed of multiple harmonic bands."""

    sample_rate: int
    duration_s: float
    bands: Sequence[HarmonicBand]
    envelope: Sequence[float] | None = None

    def _timeline(self) -> np.ndarray:
        return np.linspace(0.0, self.duration_s, int(self.sample_rate * self.duration_s), endpoint=False)

    def render(self) -> np.ndarray:
        """Render the waveform to a numpy array with amplitude in [-1, 1]."""
        t = self._timeline()
        signal = np.zeros_like(t)
        for band in self.bands:
            signal += band.sample(t)
        if self.envelope is not None:
            env = np.asarray(self.envelope, dtype=float)
            if env.size != signal.size:
                raise ValueError("Envelope length must match the rendered signal length.")
            signal *= env
        max_val = np.max(np.abs(signal))
        if max_val > 0:
            signal /= max_val
        return signal.astype(np.float32)


def golden_ratio_stack(amplitudes: Iterable[float]) -> List[float]:
    """Weight harmonics following golden ratio recursion."""
    phi = (1 + 5 ** 0.5) / 2
    weights: List[float] = []
    for i, amp in enumerate(amplitudes):
        weights.append(amp / (phi ** i))
    return weights


def breathing_envelope(sample_rate: int, duration_s: float, breaths_per_minute: float = 6.0) -> np.ndarray:
    """Build a smooth envelope synchronized to coherent breathing cycles."""
    total_samples = int(sample_rate * duration_s)
    t = np.linspace(0.0, duration_s, total_samples, endpoint=False)
    breath_freq = breaths_per_minute / 60.0
    envelope = 0.5 * (1 + np.sin(2 * np.pi * breath_freq * t - np.pi / 2))
    return envelope.astype(np.float32)


def binaural_split(program: HarmonicProgram, detune_hz: float) -> np.ndarray:
    """Render a binaural version of the program with symmetrical detuning."""
    detune_offset = detune_hz / 2.0
    t = program._timeline()
    left = np.zeros_like(t)
    right = np.zeros_like(t)
    for band in program.bands:
        lower = max(band.frequency_hz - detune_offset, 0.1)
        upper = band.frequency_hz + detune_offset
        left += band.amplitude * np.sin(2 * np.pi * lower * t + band.phase)
        right += band.amplitude * np.sin(2 * np.pi * upper * t + band.phase)
    if program.envelope is not None:
        env = np.asarray(program.envelope, dtype=float)
        left *= env
        right *= env
    stereo = np.stack([left, right], axis=1)
    max_val = np.max(np.abs(stereo))
    if max_val > 0:
        stereo /= max_val
    return stereo.astype(np.float32)
