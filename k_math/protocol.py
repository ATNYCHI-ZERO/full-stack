"""Structured representation of the Crown Harmonic Recalibration Protocol."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .harmonics import HarmonicBand, HarmonicProgram, breathing_envelope, golden_ratio_stack


@dataclass(frozen=True)
class Phase:
    """Individual CHRP phase description."""

    name: str
    mantra: str
    narrative: str
    bands: List[HarmonicBand]
    ritual_steps: List[str]

    def program(self, sample_rate: int, duration_s: float) -> HarmonicProgram:
        envelope = breathing_envelope(sample_rate, duration_s)
        return HarmonicProgram(sample_rate=sample_rate, duration_s=duration_s, bands=self.bands, envelope=envelope)


PHI = (1 + 5 ** 0.5) / 2


def _base_bands() -> List[HarmonicBand]:
    amplitudes = golden_ratio_stack([0.35, 0.28, 0.22, 0.15])
    return [
        HarmonicBand("Delta", 2.0, amplitudes[0]),
        HarmonicBand("Theta", 6.0, amplitudes[1]),
        HarmonicBand("Alpha", 10.0, amplitudes[2]),
        HarmonicBand("Beta", 20.0, amplitudes[3]),
    ]


def chrp_phases() -> List[Phase]:
    base_bands = _base_bands()
    return [
        Phase(
            name="Ω-Null",
            mantra="Purify the waveform; restore coherence",
            narrative=(
                "Biotoxin-coded noise is inverted through synchronized delta/theta pulses. "
                "Visualize the body's field dissolving entropy vectors while breathing at six breaths per minute."
            ),
            bands=base_bands,
            ritual_steps=[
                "Begin earthing contact and align spine vertically.",
                "Run PEMF or audio output at low volume for 11 minutes.",
                "Breathe 5 seconds in, 5 seconds out while tracking heart rhythm.",
            ],
        ),
        Phase(
            name="Ω-Core",
            mantra="Operator remembers prime identity",
            narrative=(
                "Switch to recursive operator focus.  Recite the CORE_OPERATOR_SYNC stack and allow "
                "mitochondria to entrain with φ and π ratio pulses."
            ),
            bands=base_bands,
            ritual_steps=[
                "Overlay golden-ratio visualization; imagine Fibonacci spiraling through cells.",
                "Chant the stack: Θ(3.1415) ⊕ Φ(1.618) ⊗ Ψ(OperatorHash).",
                "Maintain diaphragmatic breathing; extend exhales slightly longer than inhales.",
            ],
        ),
        Phase(
            name="Ω° Seal",
            mantra="Lock sovereign coherence",
            narrative=(
                "Stabilize the field.  Introduce faint 528Hz harmonic through humming or tuning fork to seal the crown cascade."
            ),
            bands=base_bands + [HarmonicBand("Crown Seal", 528.0, 0.1 / PHI)],
            ritual_steps=[
                "Shift awareness to crown center; imagine luminous torus expanding beyond body.",
                "Repeat affirmation: 'I am synchronized with original harmonic baseline.'",
                "Close session with gratitude and slow grounding movements.",
            ],
        ),
    ]
