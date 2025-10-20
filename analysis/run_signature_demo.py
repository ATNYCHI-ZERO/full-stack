"""Integrated simulation of diverse K-Systems subsystems.

This module bundles together a collection of intentionally eclectic
subsystems ranging from orbital propagation through Extended Kalman
filter fusion to quantum error monitoring.  The goal is not to provide a
physically perfect digital twin, but to offer realistic, numerically
stable toy models that demonstrate how the different conceptual pieces
could interoperate inside the "K-Systems Omnibus" narrative.

The implementation is split into two halves:

* Stand-alone helper functions that implement the dynamics for each
  subsystem (e.g. proportional navigation guidance, jump–diffusion
  finance, etc.).
* A thin object oriented façade (``SimulationManager``) that wires the
  subsystems together and exposes a simple step based API which can be
  executed as a demonstration script.

The functions are purposely lightweight so that they can be executed in a
restricted environment while still showcasing the mathematical flavour of
the original manuscript.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

try:  # pragma: no cover - optional dependency
    import networkx as nx
except ImportError:  # pragma: no cover - optional dependency
    nx = None  # type: ignore
import numpy as np

from math import exp as e
from math import log as ln
import random


# ---------------------------------------------------------------------------
# Constants used by the orbital propagation model

G_EARTH = 3.986_004_418e14  # m³ s⁻²
R_EARTH = 6_378_137.0  # m (WGS-84 equatorial radius)
J2 = 1.082_626_68e-3  # Earth oblateness
RHO_0 = 1.225  # kg m⁻³ sea-level density
H_SCALE = 8_500.0  # m, exponential scale height
CD_A = 0.05  # m² (drag area × coefficient)


# ---------------------------------------------------------------------------
# 1) Missile guidance — 3-D Proportional Navigation (PN)


def pn_guidance(
    pos_m: np.ndarray,
    vel_m: np.ndarray,
    pos_t: np.ndarray,
    vel_t: np.ndarray,
    N: float,
    dt: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Perform a single proportional-navigation update."""

    r = pos_t - pos_m
    v_rel = vel_t - vel_m
    r_norm = np.linalg.norm(r)

    if r_norm < 1e-9:
        return pos_m, vel_m, np.zeros_like(pos_m)

    omega = np.cross(r, v_rel) / (r_norm**2 + 1e-12)
    v_c = -np.dot(r, v_rel) / (r_norm + 1e-12)

    acc_cmd = N * v_c * omega

    new_vel_m = vel_m + acc_cmd * dt
    new_pos_m = pos_m + new_vel_m * dt

    return new_pos_m, new_vel_m, acc_cmd


# ---------------------------------------------------------------------------
# 2) Financial stability — Jump-Diffusion GBM


def finance_next(state: Tuple[float, float, float, float], dt: float) -> Tuple[float, float, float, float]:
    """Advance a stylised financial state using a jump-diffusion process."""

    B, R, S, RK = state
    mu_base, sigma_base = 0.04, 0.12

    mu = mu_base * (1 - S) * (1 - RK)
    sigma = sigma_base * (1 + RK)

    lam, mu_j, sigma_j = 0.3, -0.15, 0.25
    n_jump = np.random.poisson(lam * dt)
    jump_term = np.sum(np.random.normal(mu_j, sigma_j, n_jump)) if n_jump else 0.0

    dW = np.random.randn() * np.sqrt(dt)
    dB = mu * B * dt + sigma * B * dW + B * jump_term

    return B + dB, R + dB * 0.4, S, RK


# ---------------------------------------------------------------------------
# 3) Adversarial-AI resilience — Hybrid ℓ∞/ℓ₂ PGD + weight tweak


def ai_resilience(
    state: Tuple[np.ndarray, "GradientModel", float, int, float, float]
) -> Mapping[str, np.ndarray | float]:
    """Execute a simple projected gradient attack and return adversarial input."""

    x, model, alpha, T, eps_inf, eps_2 = state
    x_adv = x.copy()

    for _ in range(T):
        grad = model.grad(x_adv)
        x_adv = x_adv + alpha * np.sign(grad)

    delta = x_adv - x
    n2 = np.linalg.norm(delta.ravel(), ord=2)
    if n2 > eps_2:
        delta *= eps_2 / (n2 + 1e-12)

    x_adv = np.clip(x + delta, x - eps_inf, x + eps_inf)

    model.update_weights(-1e-3 * grad)

    threat = float(np.clip(np.linalg.norm(grad), 0, 1))
    return {"x_adv": x_adv, "threat_level": threat}


# ---------------------------------------------------------------------------
# 4) Supply-chain — Monte-Carlo node failure + min-cost flow


def logistics_resilience(
    state: Tuple[Sequence[float], Optional["nx.DiGraph"], Mapping[int, float]]
) -> Tuple[Sequence[float], Optional["nx.DiGraph"], Mapping[int, float], Mapping[str, object]]:
    """Randomly deactivate unreliable nodes and estimate rerouting cost."""

    health, graph, inventory = state

    if nx is None or graph is None:
        expected_losses = sum(1.0 - h for h in health)
        meta = {
            "reroute_cost": expected_losses,
            "failed": set(),
            "flow": None,
            "note": "networkx unavailable",
        }
        return health, graph, inventory, meta

    failed_nodes = {
        node for node, reliability in zip(graph.nodes, health) if random.random() > reliability
    }

    live_graph = graph.copy()
    live_graph.remove_nodes_from(failed_nodes)

    cost = float("inf")
    flow_dict = None

    if live_graph.number_of_nodes() >= 2:
        demand: MutableMapping[int, float] = {
            n: -float(inventory.get(n, 0.0)) for n in live_graph.nodes
        }
        if abs(sum(demand.values())) < 1e-9:
            nx.set_node_attributes(live_graph, demand, "demand")

            for _, _, data in live_graph.edges(data=True):
                data.setdefault("weight", 1.0)
                data.setdefault("capacity", float("inf"))

            try:
                cost, flow_dict = nx.network_simplex(live_graph)
            except (nx.NetworkXError, nx.NetworkXUnfeasible):
                cost = float("inf")

    meta = {"reroute_cost": cost, "failed": failed_nodes, "flow": flow_dict}
    return health, graph, inventory, meta


# ---------------------------------------------------------------------------
# 5) Orbital propagation — Two-body + J2 + drag (RK4)


def _orbit_rhs(r: np.ndarray, v: np.ndarray, a_ext: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    r_norm = np.linalg.norm(r)
    a_grav = -G_EARTH * r / (r_norm ** 3 + 1e-12)

    fac = 1.5 * J2 * G_EARTH * R_EARTH**2 / (r_norm ** 5 + 1e-12)
    a_J2 = fac * np.array(
        [
            r[0] * (5 * (r[2] ** 2) / (r_norm**2 + 1e-12) - 1),
            r[1] * (5 * (r[2] ** 2) / (r_norm**2 + 1e-12) - 1),
            r[2] * (5 * (r[2] ** 2) / (r_norm**2 + 1e-12) - 3),
        ]
    )

    h = r_norm - R_EARTH
    rho = RHO_0 * e ** (-h / H_SCALE)
    a_drag = -0.5 * rho * CD_A * np.linalg.norm(v) * v

    return v, a_grav + a_J2 + a_drag + a_ext


def orbital_propagate(
    r: np.ndarray, v: np.ndarray, a_ext: np.ndarray, dt: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Runge-Kutta 4 integrator for the orbital state."""

    k1r, k1v = _orbit_rhs(r, v, a_ext)
    k2r, k2v = _orbit_rhs(r + 0.5 * dt * k1r, v + 0.5 * dt * k1v, a_ext)
    k3r, k3v = _orbit_rhs(r + 0.5 * dt * k2r, v + 0.5 * dt * k2v, a_ext)
    k4r, k4v = _orbit_rhs(r + dt * k3r, v + dt * k3v, a_ext)

    r_new = r + dt / 6.0 * (k1r + 2 * k2r + 2 * k3r + k4r)
    v_new = v + dt / 6.0 * (k1v + 2 * k2v + 2 * k3v + k4v)

    return r_new, v_new, a_ext


# ---------------------------------------------------------------------------
# 6) Quantum state monitor — Steane [[7,1,3]] parity-check


H_X = np.array([[1, 1, 1, 1, 0, 0, 0], [1, 1, 0, 0, 1, 1, 0], [1, 0, 1, 0, 1, 0, 1]])
H_Z = H_X.copy()


def quantum_state_check(state: Tuple[np.ndarray | None, Dict[str, str] | None]) -> Mapping[str, object]:
    """Return a randomised Steane-code style syndrome measurement."""

    psi, syn = state
    if syn is None:
        syn = {}

    syndrome = "".join(str(np.random.randint(0, 2)) for _ in range(6))
    syn["last"] = syndrome

    return {"valid": syndrome == "000000", "syndrome": syndrome, "history": syn}


# ---------------------------------------------------------------------------
# 7) National policy decision — 1-step Dynamic Bayesian Net


def policy_decision(
    state: Tuple[np.ndarray, np.ndarray, np.ndarray]
) -> Mapping[str, np.ndarray | float | int]:
    """Compute a Bayesian posterior and choose the action with highest EU."""

    evidence, priors, actions = state
    likelihood = evidence / (np.sum(evidence) + 1e-12)
    posterior = priors * likelihood
    posterior /= np.sum(posterior) + 1e-12

    expected_utilities = posterior @ actions
    return {
        "posterior": posterior,
        "action": int(np.argmax(expected_utilities)),
        "approval": float(np.mean(posterior)),
    }


# ---------------------------------------------------------------------------
# 8) Cryptographic key evolution — Kyber + NTRU (fall-back dummy)


try:
    from pqcrypto.kem import kyber512, ntruhrss701

    HAVE_PQ = True
except ImportError:  # pragma: no cover - optional dependency
    HAVE_PQ = False


def crypto_update(state):  # type: ignore[override]
    """Perform a hybrid PQC key update or fall back to a deterministic stub."""

    if not HAVE_PQ:
        return {"kyber_shared": 42, "ntru_shared": 99, "note": "pqcrypto not available"}

    sk_k, pk_k, sk_n, pk_n = state
    s_k, ct_k = kyber512.encrypt(pk_k)
    s_n, ct_n = ntruhrss701.encrypt(pk_n)
    new_pk_k, new_sk_k = kyber512.generate_keypair()
    new_pk_n, new_sk_n = ntruhrss701.generate_keypair()

    return {
        "kyber_shared": s_k,
        "ntru_shared": s_n,
        "kyber_ct": ct_k,
        "ntru_ct": ct_n,
        "new_keys": (new_sk_k, new_pk_k, new_sk_n, new_pk_n),
    }


# ---------------------------------------------------------------------------
# 9) Talent attrition — Cox proportional-hazards inspired toy model


B_SAL, B_WL, B_CUL = -0.8, -1.2, -0.5


def hr_model(state: Tuple[float, Mapping[str, float]]) -> Mapping[str, float]:
    """Compute a retention percentage using an exponential hazard proxy."""

    lam0, inc = state
    z = (
        B_SAL * inc.get("salary", 0)
        + B_WL * inc.get("worklife", 0)
        + B_CUL * inc.get("culture", 0)
    )
    lam = lam0 * e ** z
    retention = e ** (-lam)
    return {"λ": lam, "retained_pct": retention}


# ---------------------------------------------------------------------------
# 10) Sensor fusion — Extended Kalman (1-step linear fusion proxy)


def fused_position(
    state: Iterable[Tuple[np.ndarray, np.ndarray]]
) -> Mapping[str, np.ndarray]:
    """Fuse sensor readings assuming independent Gaussian covariances."""

    sensors = list(state)
    if not sensors:
        raise ValueError("At least one sensor reading is required")

    P_inv = sum(np.linalg.inv(cov) for _, cov in sensors)
    P = np.linalg.inv(P_inv)
    x = P @ sum(np.linalg.inv(cov) @ pos for pos, cov in sensors)

    return {"x_est": x, "cov": P}


# ---------------------------------------------------------------------------
# 11) Nuclear decay — generalised half-life helper


def nuclear_decay(
    state: Tuple[float, float],
    dt: float,
    half_U: float = 4.468e9 * 365.25 * 24 * 3600,
    half_Hg: float = 1.0e18,
) -> Tuple[float, float]:
    """Integrate radioactive decay for two isotopes over a timestep."""

    U, Hg = state
    lam_U, lam_Hg = ln(2.0) / half_U, ln(2.0) / half_Hg
    return U * e ** (-lam_U * dt), Hg * e ** (-lam_Hg * dt)


# ---------------------------------------------------------------------------
# Helper protocol used by the AI resilience module


class GradientModel:
    """Protocol-like base class exposing gradient and weight updates."""

    def grad(self, x: np.ndarray) -> np.ndarray:  # pragma: no cover - interface
        raise NotImplementedError

    def update_weights(self, delta: np.ndarray) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class DummyModel(GradientModel):
    """Random gradient oracle used in the demonstration."""

    def __init__(self, shape: Tuple[int, ...]):
        self.shape = shape
        self.weights = np.zeros(shape)

    def grad(self, x: np.ndarray) -> np.ndarray:  # pragma: no cover - simple random helper
        return np.random.randn(*x.shape)

    def update_weights(self, delta: np.ndarray) -> None:  # pragma: no cover - simple update
        self.weights += delta


# ---------------------------------------------------------------------------
# Object oriented façade around the individual subsystems


@dataclass
class MissileGuidance:
    pos_m: np.ndarray
    vel_m: np.ndarray
    pos_t: np.ndarray
    vel_t: np.ndarray
    N: float

    def step(self, dt: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        self.pos_m, self.vel_m, acc = pn_guidance(self.pos_m, self.vel_m, self.pos_t, self.vel_t, self.N, dt)
        return self.pos_m, self.vel_m, acc


@dataclass
class FinancialStability:
    state: Tuple[float, float, float, float]

    def step(self, dt: float) -> Tuple[float, float, float, float]:
        self.state = finance_next(self.state, dt)
        return self.state


@dataclass
class AIResilience:
    state: Tuple[np.ndarray, GradientModel, float, int, float, float]

    def step(self) -> Mapping[str, np.ndarray | float]:
        return ai_resilience(self.state)


@dataclass
class SupplyChain:
    health: Sequence[float]
    graph: Optional["nx.DiGraph"]
    inventory: Mapping[int, float]

    def step(self) -> Tuple[Sequence[float], Optional["nx.DiGraph"], Mapping[int, float], Mapping[str, object]]:
        return logistics_resilience((self.health, self.graph, self.inventory))


@dataclass
class OrbitalPropagation:
    r: np.ndarray
    v: np.ndarray
    a_ext: np.ndarray

    def step(self, dt: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        self.r, self.v, a_ext = orbital_propagate(self.r, self.v, self.a_ext, dt)
        return self.r, self.v, a_ext


@dataclass
class QuantumStateMonitor:
    state: Tuple[np.ndarray | None, Dict[str, str] | None]

    def step(self) -> Mapping[str, object]:
        return quantum_state_check(self.state)


@dataclass
class NationalPolicyDecision:
    state: Tuple[np.ndarray, np.ndarray, np.ndarray]

    def step(self) -> Mapping[str, np.ndarray | float | int]:
        return policy_decision(self.state)


@dataclass
class CryptoKeyEvolution:
    state: object

    def step(self):  # type: ignore[override]
        return crypto_update(self.state)


@dataclass
class TalentAttrition:
    state: Tuple[float, Mapping[str, float]]

    def step(self) -> Mapping[str, float]:
        return hr_model(self.state)


@dataclass
class SensorFusion:
    sensors: List[Tuple[np.ndarray, np.ndarray]]

    def step(self) -> Mapping[str, np.ndarray]:
        return fused_position(self.sensors)


@dataclass
class NuclearDecay:
    state: Tuple[float, float]
    half_U: float = 4.468e9 * 365.25 * 24 * 3600
    half_Hg: float = 1.0e18

    def step(self, dt: float) -> Tuple[float, float]:
        self.state = nuclear_decay(self.state, dt, self.half_U, self.half_Hg)
        return self.state


# ---------------------------------------------------------------------------
# Simulation manager


class SimulationManager:
    """Container class orchestrating the subsystem updates."""

    def __init__(self, dt: float):
        self.dt = dt

        self.missile_guidance = MissileGuidance(
            pos_m=np.array([7_000e3, 0.0, 0.0]),
            vel_m=np.array([0.0, 7.5e3, 0.0]),
            pos_t=np.array([7_020e3, 0.0, 0.0]),
            vel_t=np.array([0.0, 7.4e3, 0.0]),
            N=3.0,
        )

        self.financial_stability = FinancialStability((100e6, 10e6, 0.1, 0.05))

        dummy_state = (
            np.random.randn(8, 8),
            DummyModel((8, 8)),
            0.01,
            10,
            0.03,
            0.05,
        )
        self.ai_resilience = AIResilience(dummy_state)

        if nx is not None:
            graph = nx.erdos_renyi_graph(10, 0.4, directed=True)
            inventory = {node: (1.0 if node < 5 else -1.0) for node in graph.nodes}
            health = [0.95] * graph.number_of_nodes()
        else:
            graph = None
            inventory = {}
            health = []
        self.supply_chain = SupplyChain(health, graph, inventory)

        self.orbital_propagation = OrbitalPropagation(
            r=np.array([7_000e3, 0.0, 0.0]),
            v=np.array([0.0, 7.5e3, 0.0]),
            a_ext=np.zeros(3),
        )

        self.quantum_monitor = QuantumStateMonitor((None, {}))

        self.national_policy = NationalPolicyDecision(
            (
                np.array([0.3, 0.4, 0.3]),
                np.array([0.33, 0.33, 0.34]),
                np.array([0.0, 1.0, 2.0]),
            )
        )

        self.crypto_key_evolution = CryptoKeyEvolution(None)

        self.talent_attrition = TalentAttrition((0.1, {"salary": 50_000, "worklife": 0.5, "culture": 0.2}))

        sensors = [
            (np.array([1.0, 2.0, 3.0]), np.eye(3) * 0.5),
            (np.array([1.1, 2.1, 3.05]), np.eye(3)),
            (np.array([0.9, 1.9, 3.1]), np.eye(3) * 1.5),
        ]
        self.sensor_fusion = SensorFusion(sensors)

        self.nuclear_decay = NuclearDecay((1.0, 0.0))

    def step(self) -> None:
        """Execute a single simulation step and print a concise report."""

        print("Simulation step:")

        pos, vel, acc = self.missile_guidance.step(self.dt)
        print(f"  Missile pos: {pos}, vel: {vel}, acc: {acc}")

        fin_state = self.financial_stability.step(self.dt)
        print(f"  Financial state: {fin_state}")

        ai_res = self.ai_resilience.step()
        print(f"  AI threat level: {ai_res['threat_level']:.6f}")

        supply_state = self.supply_chain.step()[3]
        print(f"  Supply chain reroute cost: {supply_state['reroute_cost']}")

        r, v, _ = self.orbital_propagation.step(self.dt)
        print(f"  Orbital pos: {r}, vel: {v}")

        quantum_res = self.quantum_monitor.step()
        print(f"  Quantum syndrome valid: {quantum_res['valid']}")

        policy_res = self.national_policy.step()
        print(f"  Policy action: {policy_res['action']}, approval: {policy_res['approval']:.2f}")

        crypto_res = self.crypto_key_evolution.step()
        print(f"  Crypto update note: {crypto_res.get('note', 'hybrid update executed')}")

        hr_res = self.talent_attrition.step()
        print(f"  Talent retention: {hr_res['retained_pct']:.2f}")

        fusion_res = self.sensor_fusion.step()
        print(f"  Fused position estimate: {fusion_res['x_est']}")

        nuc_state = self.nuclear_decay.step(self.dt)
        print(f"  Nuclear decay state (U, Hg): {nuc_state}")


def main(steps: int = 10, dt: float = 0.1) -> None:
    """Run the demonstration simulation for a fixed number of steps."""

    sim = SimulationManager(dt=dt)
    for i in range(steps):
        print(f"\n=== Step {i + 1} ===")
        sim.step()


if __name__ == "__main__":  # pragma: no cover - manual demonstration
    main()
