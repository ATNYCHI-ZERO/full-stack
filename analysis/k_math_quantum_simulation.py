"""Utility for simulating a stochastic-harmonic hybrid process.

This script reimplements the exploratory notebook code that combined a
harmonic oscillator model ("K-Math" terminology) with stochastic quantum
fluctuations.  The goal is to make the experiment reproducible from the
command line and to keep the core simulation code free from optional
non-standard imports until the results have been generated.

Running the module as a script generates a PNG plot showing a single run
of the process alongside the ensemble mean and one standard deviation
band.  A CSV snapshot with the first few rows of key statistics is also
written to disk so that automated tools (or humans) can quickly inspect
numerical values without re-running the simulation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence, Tuple

import argparse
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

ArrayLike = np.ndarray


@dataclass
class SimulationResult:
    """Container for a single simulation run."""

    t: ArrayLike
    omega: ArrayLike
    omega_rcf: ArrayLike
    qnoise: ArrayLike
    signal: ArrayLike
    key_material: ArrayLike


@dataclass
class EnsembleResult:
    """Aggregate statistics for multiple runs of the process."""

    mean_signal: ArrayLike
    var_signal: ArrayLike
    mean_key: ArrayLike
    var_key: ArrayLike
    all_signal: ArrayLike
    all_keys: ArrayLike


def omega_operator(
    t: ArrayLike,
    freqs: Sequence[float] = (50.0, 120.0, 240.0),
    amps: Sequence[float] = (1.0, 0.5, 0.25),
    phases: Optional[Sequence[float]] = None,
) -> ArrayLike:
    """Compute the harmonic operator as a sum of sinusoids."""

    if phases is None:
        phases = (0.0,) * len(freqs)
    if len(freqs) != len(amps) or len(freqs) != len(phases):
        raise ValueError("freqs, amps, and phases must have the same length")
    out = np.zeros_like(t, dtype=float)
    for freq, amp, phi in zip(freqs, amps, phases):
        out += amp * np.sin(2 * np.pi * freq * t + phi)
    return out


def rcf_operator(x: ArrayLike, alpha: float = 0.8, beta: float = 0.1) -> ArrayLike:
    """Apply the Recursive Crown Function (RCF) filter."""

    if not 0 <= alpha <= 1:
        raise ValueError("alpha must lie in [0, 1]")
    y = np.zeros_like(x, dtype=float)
    y[0] = x[0]
    for i in range(1, len(x)):
        y[i] = alpha * y[i - 1] + (1 - alpha) * x[i] + beta * np.tanh(x[i])
    return y


def quantum_noise(
    t: ArrayLike,
    *,
    rng: np.random.Generator,
    sigma: float = 0.02,
    spike_rate: float = 0.005,
    spike_amp: float = 0.5,
) -> ArrayLike:
    """Generate quantum-like noise with occasional spikes."""

    base = rng.normal(0.0, sigma, size=t.shape)
    spikes = rng.random(size=t.shape) < spike_rate
    if np.any(spikes):
        base[spikes] += rng.normal(spike_amp, spike_amp * 0.3, size=int(spikes.sum()))
    return base


def harmonic_kdf(*components: ArrayLike) -> ArrayLike:
    """Non-linearly mix components into a normalized scalar sequence."""

    if not components:
        raise ValueError("At least one component is required")
    mix = np.zeros_like(components[0], dtype=float)
    for comp in components:
        mix = mix + np.arctan(comp)
    denom = np.max(np.abs(mix)) + 1e-12
    return mix / denom


def simulate_run(
    t: ArrayLike,
    *,
    rng: np.random.Generator,
    rcf_alpha: float = 0.85,
    rcf_beta: float = 0.08,
    noise_sigma: float = 0.02,
    noise_spike_rate: float = 0.003,
    noise_spike_amp: float = 0.4,
) -> SimulationResult:
    """Simulate one stochastic-harmonic trajectory."""

    phases = rng.normal(0.0, 0.1, size=3)
    omega = omega_operator(t, phases=phases)
    omega_rcf = rcf_operator(omega, alpha=rcf_alpha, beta=rcf_beta)
    qnoise = quantum_noise(
        t,
        rng=rng,
        sigma=noise_sigma,
        spike_rate=noise_spike_rate,
        spike_amp=noise_spike_amp,
    )
    signal = omega_rcf + qnoise
    key_material = harmonic_kdf(omega_rcf, qnoise)
    return SimulationResult(
        t=t,
        omega=omega,
        omega_rcf=omega_rcf,
        qnoise=qnoise,
        signal=signal,
        key_material=key_material,
    )


def ensemble_simulations(
    t: ArrayLike,
    runs: int,
    *,
    rng: np.random.Generator,
    simulation_kwargs: Optional[Dict[str, float]] = None,
) -> Tuple[EnsembleResult, SimulationResult]:
    """Run an ensemble of simulations and compute summary statistics."""

    if runs <= 0:
        raise ValueError("runs must be a positive integer")

    simulation_kwargs = simulation_kwargs or {}
    all_signal = np.zeros((runs, t.size), dtype=float)
    all_keys = np.zeros((runs, t.size), dtype=float)
    last_sample: Optional[SimulationResult] = None

    for i in range(runs):
        run_rng = np.random.default_rng(rng.integers(1, 2**31 - 1))
        result = simulate_run(t, rng=run_rng, **simulation_kwargs)
        all_signal[i, :] = result.signal
        all_keys[i, :] = result.key_material
        last_sample = result

    assert last_sample is not None  # for type checkers
    mean_signal = all_signal.mean(axis=0)
    var_signal = all_signal.var(axis=0)
    mean_key = all_keys.mean(axis=0)
    var_key = all_keys.var(axis=0)

    ensemble = EnsembleResult(
        mean_signal=mean_signal,
        var_signal=var_signal,
        mean_key=mean_key,
        var_key=var_key,
        all_signal=all_signal,
        all_keys=all_keys,
    )
    return ensemble, last_sample


def plot_results(
    t: ArrayLike,
    sample: SimulationResult,
    ensemble: EnsembleResult,
    *,
    output_path: Path,
) -> None:
    """Create and save the comparison plot."""

    plt.figure(figsize=(10, 5))
    plt.plot(sample.t, sample.signal, label="One run S(t)")
    plt.plot(t, ensemble.mean_signal, label="Ensemble mean S(t)", linewidth=2)
    std = np.sqrt(ensemble.var_signal)
    plt.fill_between(t, ensemble.mean_signal - std, ensemble.mean_signal + std, alpha=0.2)
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude (arb units)")
    plt.title("Stochastic-Harmonic Signal: sample run and ensemble mean ± stddev")
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()


def snapshot_dataframe(
    t: ArrayLike,
    sample: SimulationResult,
    ensemble: EnsembleResult,
    *,
    rows: int = 10,
) -> pd.DataFrame:
    """Construct a small dataframe summarizing early time points."""

    std_signal = np.sqrt(ensemble.var_signal)
    std_key = np.sqrt(ensemble.var_key)
    return pd.DataFrame(
        {
            "t": t[:rows],
            "sample_signal": sample.signal[:rows],
            "mean_signal": ensemble.mean_signal[:rows],
            "std_signal": std_signal[:rows],
            "sample_key": sample.key_material[:rows],
            "mean_key": ensemble.mean_key[:rows],
            "std_key": std_key[:rows],
        }
    )


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fs", type=float, default=1000.0, help="Sampling frequency in Hz")
    parser.add_argument("--duration", type=float, default=1.0, help="Simulation duration in seconds")
    parser.add_argument("--runs", type=int, default=200, help="Number of ensemble runs to average")
    parser.add_argument("--seed", type=int, default=20251020, help="Seed for the ensemble RNG")
    parser.add_argument(
        "--plot-path",
        type=Path,
        default=Path("analysis/output/k_math_quantum_simulation.png"),
        help="Location to save the plot PNG",
    )
    parser.add_argument(
        "--snapshot-csv",
        type=Path,
        default=Path("analysis/output/k_math_quantum_snapshot.csv"),
        help="Location to write the snapshot CSV",
    )
    parser.add_argument(
        "--snapshot-rows",
        type=int,
        default=10,
        help="Number of rows to include in the snapshot CSV",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_args(argv)
    dt = 1.0 / args.fs
    t = np.arange(0.0, args.duration, dt)
    if t.size == 0:
        raise ValueError("The generated time array is empty; check fs and duration")

    ensemble_rng = np.random.default_rng(args.seed)
    ensemble, sample = ensemble_simulations(t, args.runs, rng=ensemble_rng)
    plot_results(t, sample, ensemble, output_path=args.plot_path)

    df = snapshot_dataframe(t, sample, ensemble, rows=args.snapshot_rows)
    args.snapshot_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.snapshot_csv, index=False)

    # Provide a concise textual summary for CLI usage.
    print(f"Saved plot to: {args.plot_path}")
    print(f"Snapshot CSV written to: {args.snapshot_csv}")
    print(df.head().to_string(index=False))


if __name__ == "__main__":  # pragma: no cover - script execution entry point
    main()
