"""Numerical exploration of the bounded chaos meta-system without external dependencies."""
from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Callable, List, Sequence, Tuple


@dataclass
class SimulationConfig:
    x: float = 2.0
    z: complex = 1j
    H0: float = 1.0
    sigma: float = 1.0
    t_end: float = 10.0
    dt: float = 0.01
    psi_iterations: int = 4
    truncate: float = 6.0


def frange(start: float, stop: float, step: float) -> List[float]:
    values: List[float] = []
    current = start
    while current < stop + 0.5 * step:
        values.append(current)
        current += step
    return values


def gaussian_density(x: float, sigma: float) -> float:
    coefficient = 1.0 / (sigma * math.sqrt(2.0 * math.pi))
    exponent = -0.5 * (x / sigma) ** 2
    return coefficient * math.exp(exponent)


def entropic_curvature(x: float, density: Callable[[float], float], dx: float = 1e-3) -> float:
    log_forward = math.log(density(x + dx))
    log_central = math.log(density(x))
    log_backward = math.log(density(x - dx))
    second_derivative = (log_forward - 2.0 * log_central + log_backward) / (dx**2)
    return -second_derivative


def solve_harmonic_term(config: SimulationConfig) -> Tuple[List[float], List[float]]:
    t_values = frange(0.0, config.t_end, config.dt)
    H_values: List[float] = [config.H0]
    for _ in range(1, len(t_values)):
        previous = H_values[-1]
        derivative = 0.5 * (previous + 1.0 / previous)
        H_values.append(previous + config.dt * derivative)
    harmonic = [0.5 * (value + 1.0 / value) for value in H_values]
    return t_values, harmonic


def cumulative_integral(values: Sequence[complex], step: float) -> List[complex]:
    total: complex = 0j
    result: List[complex] = []
    for value in values:
        total += value * step
        result.append(total)
    return result


def interpolate(tau: Sequence[float], psi: Sequence[complex], targets: Sequence[float]) -> List[complex]:
    result: List[complex] = []
    for target in targets:
        if target <= tau[0]:
            result.append(psi[0])
            continue
        if target >= tau[-1]:
            result.append(psi[-1])
            continue
        low = 0
        high = len(tau) - 1
        while high - low > 1:
            mid = (low + high) // 2
            if tau[mid] <= target:
                low = mid
            else:
                high = mid
        ratio = (target - tau[low]) / (tau[high] - tau[low])
        interpolated = psi[low] + (psi[high] - psi[low]) * ratio
        result.append(interpolated)
    return result


def build_recursive_psi(config: SimulationConfig, t_values: Sequence[float]) -> List[complex]:
    tau = frange(-config.truncate, config.t_end, config.dt)
    psi: List[complex] = [complex(value, 0.0) for value in tau]
    step = config.dt
    for _ in range(config.psi_iterations):
        integrand = [cmath.exp(1j * value) for value in psi]
        psi = cumulative_integral(integrand, step)
    return interpolate(tau, psi, t_values)


def solve_chrono_fold(config: SimulationConfig, t_values: Sequence[float]) -> List[complex]:
    C_values: List[complex] = [0j]
    for _ in range(1, len(t_values)):
        derivative = cmath.exp(1j * C_values[-1])
        C_values.append(C_values[-1] + config.dt * derivative)
    integrand = [cmath.exp(1j * value) for value in C_values]
    return cumulative_integral(integrand, config.dt)


def simulate(config: SimulationConfig = SimulationConfig()) -> Tuple[List[float], List[complex]]:
    t_values, harmonic = solve_harmonic_term(config)
    reflective = config.x ** (config.x - 1.0)
    inversion = config.z ** 2 + 1.0 / config.z.conjugate()
    curvature = entropic_curvature(config.x, lambda value: gaussian_density(value, config.sigma))
    psi_values = build_recursive_psi(config, t_values)
    psi_integral = cumulative_integral([cmath.exp(1j * value) for value in psi_values], config.dt)
    chrono_integral = solve_chrono_fold(config, t_values)
    phi: List[complex] = []
    for idx, harmonic_term in enumerate(harmonic):
        value = (
            harmonic_term
            * reflective
            * inversion
            * curvature
            * psi_integral[idx]
            * chrono_integral[idx]
        )
        phi.append(value)
    return t_values, phi


def magnitude(values: Sequence[complex]) -> List[float]:
    return [abs(value) for value in values]


def phase(values: Sequence[complex]) -> List[float]:
    phases: List[float] = []
    previous = 0.0
    for value in values:
        angle = cmath.phase(value)
        # unwrap
        while angle - previous > math.pi:
            angle -= 2.0 * math.pi
        while previous - angle > math.pi:
            angle += 2.0 * math.pi
        phases.append(angle)
        previous = angle
    return phases


def main() -> None:
    config = SimulationConfig()
    t_values, phi = simulate(config)
    mags = magnitude(phi)
    phases = phase(phi)
    print("time final_value magnitude phase")
    print(f"{t_values[-1]:6.3f} {phi[-1]: .6f} {mags[-1]: .6f} {phases[-1]: .6f}")
    print(
        "Sample statistics:",
        f"|Phi| min={min(mags):.6f}",
        f"max={max(mags):.6f}",
        f"mean={sum(mags) / len(mags):.6f}",
    )


if __name__ == "__main__":
    main()
