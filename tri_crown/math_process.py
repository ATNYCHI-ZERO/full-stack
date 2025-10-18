"""Analytical helpers for the TRI-CROWN Math/Process annex.

The functions collected in this module translate each section of the
annex into an executable counterpart.  The implementation favours
clarity and numerical robustness over strict performance so that the
helpers can be embedded in reference or test harnesses without pulling
in heavy external dependencies.  When SciPy is available it is used for
matrix exponentials and discrete Riccati solves; otherwise carefully
chosen fallbacks are employed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Tuple

import hashlib
import math
import string

import numpy as np

try:  # pragma: no cover - exercised indirectly in environments with SciPy.
    from scipy.linalg import expm, solve_discrete_are
except Exception:  # pragma: no cover - SciPy is optional.
    expm = None  # type: ignore[assignment]
    solve_discrete_are = None  # type: ignore[assignment]


def _series_expm(A: np.ndarray, dt: float, order: int = 6) -> np.ndarray:
    """Compute a matrix exponential via a truncated Taylor series.

    The helper is used only as a fallback when SciPy is unavailable.  A
    sixth-order Taylor approximation is sufficient for the small
    time-steps employed in TRI-CROWN's process layer.  The scaling and
    squaring trick keeps the result stable for moderate norms of
    ``A * dt``.
    """

    M = A * dt
    # Scaling and squaring for stability.
    norm = np.linalg.norm(M, ord=np.inf)
    if norm == 0:
        s = 0
    else:
        s = max(0, int(math.log2(norm)) - 1)
    M_scaled = M / (2**s if s > 0 else 1)

    term = np.eye(A.shape[0])
    result = term.copy()
    for k in range(1, order + 1):
        term = term @ M_scaled / k
        result = result + term

    for _ in range(s):
        result = result @ result
    return result


def matrix_exponential(A: np.ndarray, dt: float) -> np.ndarray:
    """Return ``exp(A * dt)`` using SciPy when available.

    Parameters
    ----------
    A:
        Square system matrix.
    dt:
        Time step in seconds.
    """

    if expm is not None:
        return expm(A * dt)
    return _series_expm(A, dt)


@dataclass(frozen=True)
class ProcessDiscretisation:
    """Discrete process model produced from continuous system matrices."""

    phi: np.ndarray
    gamma: np.ndarray
    state_trajectory: np.ndarray


def _compute_gamma(A: np.ndarray, B: np.ndarray, dt: float, phi: np.ndarray) -> np.ndarray:
    """Compute the discretised inhomogeneous term."""

    if expm is not None:
        # Use the block matrix trick to get the exact integral.
        n, m = A.shape[0], B.shape[1]
        block = np.block([
            [A, B],
            [np.zeros((m, n)), np.zeros((m, m))],
        ]) * dt
        exp_block = expm(block)
        return exp_block[:n, n:]

    # Fallback: composite Simpson's rule with modest resolution.
    sub_steps = 8
    gamma = np.zeros_like(B)
    for i in range(sub_steps + 1):
        tau = dt * i / sub_steps
        weight = 2 + 2 * (i % 2 == 1)
        if i in (0, sub_steps):
            weight = 1
        gamma += weight * matrix_exponential(A, dt - tau) @ B
    gamma *= dt / (3 * sub_steps)
    return gamma


def green_convolution(
    A: np.ndarray,
    B: np.ndarray,
    controls: np.ndarray,
    dt: float,
    initial_state: np.ndarray | None = None,
) -> ProcessDiscretisation:
    """Discretise the continuous-time process layer.

    The function corresponds to Section A of the annex.  It evaluates the
    state transition matrix ``Phi`` and the discretised convolution term
    ``Gamma`` and uses them to propagate the state trajectory under a
    zero-order hold assumption for the control inputs.
    """

    if controls.ndim != 2:
        raise ValueError("controls must be a 2-D array with shape (T, m)")
    n = A.shape[0]
    phi = matrix_exponential(A, dt)
    gamma = _compute_gamma(A, B, dt, phi)

    steps = controls.shape[0]
    trajectory = np.zeros((steps + 1, n)) if initial_state is None else np.zeros((steps + 1, n), dtype=float)
    if initial_state is not None:
        trajectory[0] = initial_state
    gb = gamma @ controls.T
    for k in range(steps):
        trajectory[k + 1] = phi @ trajectory[k] + gb[:, k]

    return ProcessDiscretisation(phi=phi, gamma=gamma, state_trajectory=trajectory)


def modal_coordinates(A: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return the eigenvector matrix and diagonal modal matrix of ``A``."""

    eigvals, eigvecs = np.linalg.eig(A)
    V = eigvecs
    V_inv = np.linalg.inv(V)
    Lambda = np.diag(eigvals)
    return V, Lambda


def riccati_gain(
    A: np.ndarray,
    B: np.ndarray,
    Q: np.ndarray,
    R: np.ndarray,
    *,
    tolerance: float = 1e-10,
    max_iterations: int = 10_000,
) -> Tuple[np.ndarray, np.ndarray]:
    """Solve the discrete Riccati equation for the LQR feedback gain.

    The discrete-time algebraic Riccati equation yields the optimal cost
    matrix ``P`` and corresponding feedback gain ``K``.  SciPy's
    :func:`solve_discrete_are` is used when present; otherwise an
    iterative Kleinman algorithm is applied.
    """

    if solve_discrete_are is not None:
        P = solve_discrete_are(A, B, Q, R)
        S = B.T @ P @ B + R
        K = np.linalg.solve(S, B.T @ P @ A)
        return K, P

    P = Q.copy()
    for _ in range(max_iterations):
        S = B.T @ P @ B + R
        K = np.linalg.solve(S, B.T @ P @ A)
        P_next = Q + A.T @ P @ (A - B @ K)
        if np.linalg.norm(P_next - P, ord=np.inf) < tolerance:
            P = P_next
            break
        P = P_next
    return K, P


def compose_process_and_wave(phi: np.ndarray, wave_operator: np.ndarray) -> np.ndarray:
    """Construct the block-diagonal composite propagation operator."""

    return np.block([
        [phi, np.zeros((phi.shape[0], wave_operator.shape[1]))],
        [np.zeros((wave_operator.shape[0], phi.shape[1])), wave_operator],
    ])


def causal_convolution(phi: np.ndarray, gamma: np.ndarray, controls: np.ndarray) -> np.ndarray:
    """Evaluate the causal Green's function convolution for Section C."""

    steps = controls.shape[0]
    result = np.zeros((steps, phi.shape[0]))
    for k in range(steps):
        acc = np.zeros(phi.shape[0])
        for j in range(k + 1):
            acc += np.linalg.matrix_power(phi, k - j) @ (gamma @ controls[j])
        result[k] = acc
    return result


def fourier_energy_ratios(signal: np.ndarray, *, num_bands: int = 4) -> np.ndarray:
    """Return normalised Fourier-band energy ratios.

    The vector is invariant to overall scaling and therefore dimensionless.
    """

    if signal.ndim != 1:
        raise ValueError("signal must be one-dimensional")
    spectrum = np.abs(np.fft.rfft(signal)) ** 2
    total = spectrum.sum()
    if total == 0:
        return np.zeros(num_bands)
    bins = np.array_split(spectrum, num_bands)
    energies = np.array([band.sum() for band in bins])
    return energies / total


_ALPHA = string.ascii_lowercase


def apply_caesar_shift(text: str, shift: int) -> str:
    """Apply a Caesar shift in the lowercase Latin alphabet."""

    result = []
    for ch in text:
        idx = _ALPHA.find(ch.lower())
        if idx == -1:
            result.append(ch)
            continue
        shifted = _ALPHA[(idx + shift) % 26]
        result.append(shifted if ch.islower() else shifted.upper())
    return "".join(result)


def reverse_letters(text: str) -> str:
    """Return the text reversed character by character."""

    return text[::-1]


def bigram_probabilities(text: str) -> Mapping[Tuple[str, str], float]:
    """Compute empirical bigram probabilities for lowercase letters."""

    cleaned = [ch for ch in text.lower() if ch in _ALPHA or ch == " "]
    cleaned_text = "".join(cleaned).replace(" ", "_")
    if len(cleaned_text) < 2:
        return {}
    counts: dict[Tuple[str, str], int] = {}
    for a, b in zip(cleaned_text, cleaned_text[1:]):
        counts[(a, b)] = counts.get((a, b), 0) + 1
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}


_INTERROGATIVES = {"who", "what", "when", "where", "why", "how", "?"}


def interrogative_score(text: str) -> int:
    """Count interrogative markers in the supplied text."""

    lower = text.lower()
    return sum(lower.count(marker) for marker in _INTERROGATIVES)


@dataclass
class HuberResult:
    coefficients: np.ndarray
    scale: float


def _huber_weights(residuals: np.ndarray, delta: float) -> np.ndarray:
    abs_res = np.abs(residuals)
    weights = np.ones_like(abs_res)
    mask = abs_res > delta
    weights[mask] = delta / np.maximum(abs_res[mask], 1e-12)
    return weights


def huber_irls(
    X: np.ndarray,
    y: np.ndarray,
    *,
    delta: float = 1.0,
    max_iterations: int = 50,
    tolerance: float = 1e-10,
) -> HuberResult:
    """Perform Huber M-estimation using Iteratively Reweighted Least Squares."""

    if X.ndim != 2:
        raise ValueError("X must be two-dimensional")
    if y.ndim != 1:
        raise ValueError("y must be one-dimensional")
    if X.shape[0] != y.shape[0]:
        raise ValueError("X and y dimensions are inconsistent")

    beta = np.zeros(X.shape[1])
    for _ in range(max_iterations):
        residuals = y - X @ beta
        weights = _huber_weights(residuals, delta)
        W = np.diag(weights)
        XtW = X.T @ W
        regulariser = 1e-8 * np.eye(X.shape[1])
        beta_next = np.linalg.solve(XtW @ X + regulariser, XtW @ y)
        if np.linalg.norm(beta_next - beta) < tolerance:
            beta = beta_next
            break
        beta = beta_next
    mad = np.median(np.abs(y - X @ beta))
    scale = mad / 0.6745 if mad > 0 else 0.0
    return HuberResult(coefficients=beta, scale=scale)


_DEF_CONTEXT = b"tri-crown"


def fixed_point_key_binding(
    seed: bytes,
    *,
    context: bytes = _DEF_CONTEXT,
    features: Iterable[bytes] = (),
    rounds: int = 8,
) -> Tuple[bytes, bytes]:
    """Derive a fixed-point key binding and its commitment digest."""

    feature_digest = hashlib.sha3_256(b"".join(features)).digest()
    key = hashlib.sha3_512(seed + context).digest()
    for _ in range(rounds):
        key = hashlib.sha3_512(key + context + feature_digest).digest()
    commitment = hashlib.sha3_256(key + feature_digest).digest()
    return key, commitment


@dataclass(frozen=True)
class FeatureDigests:
    fourier: np.ndarray
    bigrams: Mapping[Tuple[str, str], float]
    interrogatives: int
    raw_digest: bytes


def features_digest(
    phi: np.ndarray,
    gamma: np.ndarray,
    wave_operator: np.ndarray,
    text: str,
    *,
    fourier_source: np.ndarray | None = None,
) -> FeatureDigests:
    """Create the digest used as additional salt in Section G."""

    fourier = fourier_energy_ratios(fourier_source if fourier_source is not None else phi.flatten())
    bigrams = bigram_probabilities(text)
    inter_score = interrogative_score(text)

    bigram_blob = b"".join(
        f"{a}{b}:{prob:.6f}|".encode("utf-8") for (a, b), prob in sorted(bigrams.items())
    )
    payload = (
        phi.astype(np.float64).tobytes()
        + gamma.astype(np.float64).tobytes()
        + wave_operator.astype(np.float64).tobytes()
        + fourier.astype(np.float64).tobytes()
        + bigram_blob
        + str(inter_score).encode("utf-8")
    )
    raw = hashlib.sha3_256(payload).digest()
    return FeatureDigests(fourier=fourier, bigrams=bigrams, interrogatives=inter_score, raw_digest=raw)


_DEF_MATH_SALT_CTX = b"tri-crown-math-salt"


def math_salt(
    phi: np.ndarray,
    gamma: np.ndarray,
    wave_operator: np.ndarray,
    text: str,
    *,
    fourier_source: np.ndarray | None = None,
    hkdf_context: bytes = _DEF_MATH_SALT_CTX,
) -> Tuple[bytes, FeatureDigests]:
    """Compute the annex salt and return it alongside the structured features."""

    digests = features_digest(
        phi,
        gamma,
        wave_operator,
        text,
        fourier_source=fourier_source,
    )
    math_digest = hashlib.sha3_256(hkdf_context + digests.raw_digest).digest()
    return math_digest, digests
