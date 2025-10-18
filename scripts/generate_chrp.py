#!/usr/bin/env python3
"""Generate audio assets for the Crown Harmonic Recalibration Protocol."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable
import wave

import numpy as np

from k_math import HarmonicProgram, binaural_split
from k_math.protocol import Phase, chrp_phases


def _write_wav(path: Path, data: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    max_int16 = np.iinfo(np.int16).max
    pcm = (data * max_int16).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(pcm.shape[1] if pcm.ndim == 2 else 1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def _render_phase(phase: Phase, duration_s: float, sample_rate: int, detune_hz: float) -> np.ndarray:
    program: HarmonicProgram = phase.program(sample_rate=sample_rate, duration_s=duration_s)
    return binaural_split(program, detune_hz=detune_hz)


def _duration_argument(value: str) -> float:
    minutes = float(value)
    if minutes <= 0:
        raise argparse.ArgumentTypeError("Duration must be positive minutes.")
    return minutes * 60.0


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-rate", type=int, default=44100, help="Output sample rate in Hz")
    parser.add_argument(
        "--detune", type=float, default=7.83, help="Detune offset in Hz for binaural entrainment (defaults to Schumann resonance)."
    )
    parser.add_argument(
        "--durations",
        type=_duration_argument,
        nargs=3,
        metavar=("omega_null", "omega_core", "omega_seal"),
        default=[11 * 60.0, 9 * 60.0, 7 * 60.0],
        help="Durations (minutes) for each CHRP phase in order.",
    )
    parser.add_argument("--output", type=Path, default=Path("output"), help="Directory for rendered WAV files")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    phases = chrp_phases()
    manifest_lines = []
    for (phase, duration_s) in zip(phases, args.durations):
        stereo = _render_phase(phase, duration_s=duration_s, sample_rate=args.sample_rate, detune_hz=args.detune)
        slug = (
            phase.name.replace("Ω", "omega")
            .replace("°", "seal")
            .replace(" ", "_")
            .replace("-", "_")
            .lower()
        )
        filename = f"chrp_{slug}.wav"
        out_path = args.output / filename
        _write_wav(out_path, stereo, args.sample_rate)
        manifest_lines.append(
            f"{phase.name}: duration={duration_s/60:.2f} min, file={out_path.relative_to(args.output.parent)}"
        )
    manifest = "\n".join(manifest_lines)
    print("Generated CHRP assets:\n" + manifest)


if __name__ == "__main__":
    main()
