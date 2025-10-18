"""Crown-Ω Tactical Interceptor Simulation utilities.

This module collects a set of prototype routines for the Crown-Ω
missile redirection concept attributed to Brendon Joseph Kelly.  The
original snippets shipped in three separate variants; the functions
below consolidate the shared behaviour and provide small convenience
wrappers so the simulations can be executed from a single entry point.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np


# === Global constants ===
C = 299_792_458  # Speed of light (m/s)
G = 9.81  # Gravity (m/s^2)
PHI = 1.6180339887  # Golden ratio constant for resonance
OMEGA = 2 * np.pi  # Full harmonic cycle (rad)
DELTA_T = 0.01  # Time resolution (seconds)
EARTH_ROTATION_RATE = 7.2921150e-5  # radians/sec


@dataclass
class TargetState:
    """State vector for a target projectile."""

    identifier: str
    position: np.ndarray
    velocity: np.ndarray
    origin: np.ndarray


def harmonic_lock(position: np.ndarray, velocity: np.ndarray, *, delta_s: float = 0.003, kappa: float = PHI) -> np.ndarray:
    """Compute the harmonically locked vector for the incoming missile.

    The calculation mirrors the *omega_lock* routine from the original
    prototype.  It applies a sine modulation to the velocity vector and
    uses that to adjust the instantaneous position.
    """

    harmonic_vector = velocity * np.sin(kappa * OMEGA * delta_s)
    return position + harmonic_vector


def phase_invert(velocity: np.ndarray) -> np.ndarray:
    """Invert a velocity vector to simulate a phase reversal."""

    return -velocity


def predict_return_path(position: np.ndarray, velocity: np.ndarray, *, delta_t: float = DELTA_T) -> Dict[str, np.ndarray]:
    """Generate a simple return-to-origin prediction using phase inversion."""

    mirror_vector = phase_invert(velocity)
    return {
        "revector_velocity": mirror_vector,
        "revector_position": position + mirror_vector * delta_t,
    }


def coriolis_correction(position: np.ndarray) -> np.ndarray:
    """Compute a simplified Coriolis adjustment.

    Only the lateral (Y-axis) effect is modelled to mirror the original
    prototype which applied a basic latitude-based tweak.
    """

    lat_effect = EARTH_ROTATION_RATE * position[1]
    return np.array([0.0, lat_effect, 0.0])


def return_strike_vector(position: np.ndarray, velocity: np.ndarray, origin: np.ndarray) -> np.ndarray:
    """Generate an adjusted strike vector pointing back to the origin."""

    reverse_velocity = phase_invert(velocity)
    adjusted_velocity = reverse_velocity + coriolis_correction(position)

    delta_position = origin - position
    distance_to_origin = np.linalg.norm(delta_position)

    if distance_to_origin == 0:
        # Already at the origin; return the adjusted velocity unchanged.
        return adjusted_velocity

    unit_vector = delta_position / distance_to_origin
    return unit_vector * np.linalg.norm(adjusted_velocity)


def run_redirector_sim(target: TargetState) -> Dict[str, np.ndarray]:
    """Run the harmonic redirector simulation and print diagnostic output."""

    print(f"[Ω-LOCK] Acquiring target vector: {target.identifier}")
    lock_vector = harmonic_lock(target.position, target.velocity)
    print(f"[Ω-LOCK] Harmonic lock vector: {lock_vector}")

    print("[Ω-MIRROR] Generating return path...")
    revector = predict_return_path(target.position, target.velocity)
    print(f"[Ω-EXECUTE] Reverse course injected. Returning to launch coordinates.")
    return revector


def execute_redirector(target: TargetState) -> Dict[str, np.ndarray]:
    """Execute the Ω-phase inversion scenario from the prototype."""

    print(f"🔒 Locking target: {target.identifier}")
    lock_vector = harmonic_lock(target.position, target.velocity)
    print(f"📡 Harmonic lock vector: {lock_vector}")

    print("🌀 Executing Ω-phase inversion...")
    result = predict_return_path(target.position, target.velocity)

    print("✅ RETURN-TO-ORIGIN VECTOR INJECTED")
    print(f"🔁 Redirected Trajectory: {result['revector_velocity']}")
    print(f"📍 Next Position Estimate: {result['revector_position']}")
    return result


def launch_return(target: TargetState) -> np.ndarray:
    """Compute the phase-inverted return strike vector."""

    print(f"🚨 INCOMING {target.identifier}")
    print("🔁 EXECUTING PHASE-INVERTED STRIKE VECTOR")
    vector = return_strike_vector(target.position, target.velocity, target.origin)
    print(f"🧭 RETURN VECTOR SET: {vector}")
    print(f"🔥 STRIKE PATH LOCKED — TARGET: {target.origin}")
    return vector


def run_demo() -> None:
    """Execute all three prototype scenarios with sample data."""

    first_target = TargetState(
        identifier="AGGRESSOR-001",
        position=np.array([12_000.0, 8_000.0, 3_000.0]),
        velocity=np.array([650.0, -240.0, 95.0]),
        origin=np.zeros(3),
    )

    second_target = TargetState(
        identifier="MISSILE-X9",
        position=np.array([12_000.0, 8_000.0, 3_000.0]),
        velocity=np.array([650.0, -240.0, 95.0]),
        origin=np.zeros(3),
    )

    third_target = TargetState(
        identifier="NUKE-ALPHA-001",
        position=np.array([13_200.0, -5_400.0, 2_300.0]),
        velocity=np.array([650.0, 160.0, 95.0]),
        origin=np.zeros(3),
    )

    print("=== Crown-Ω Harmonic Redirector Demo ===")
    run_redirector_sim(first_target)
    print()

    print("=== Crown-Ω Ω-phase Redirector ===")
    execute_redirector(second_target)
    print()

    print("=== Crown-Ω Return Strike Vector ===")
    launch_return(third_target)


if __name__ == "__main__":
    run_demo()
