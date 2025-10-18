"""Linear-systems and text/cipher helpers for the TRI-CROWN annexes."""
from __future__ import annotations

from typing import Callable, List, Tuple

import numpy as np

try:  # Prefer SciPy when available for numerical robustness.
    from scipy.linalg import expm  # type: ignore
except Exception:  # pragma: no cover - SciPy is optional.
    expm = None  # type: ignore


def _matrix_exponential(a: np.ndarray) -> np.ndarray:
    """Return the matrix exponential of ``a``.

    A light-weight scaling-and-squaring implementation is provided as a
    fallback when SciPy is unavailable.  The routine is adapted from the
    (13,13) Pade approximation in Higham (2005).
    """

    if expm is not None:  # pragma: no branch - fast path when SciPy exists.
        return expm(a)

    # Scaling and squaring with a (13,13) Pade approximant.  The
    # coefficients are taken from table 2 of Higham, 2005.
    b = (
        64764752532480000.0,
        32382376266240000.0,
        7771770303897600.0,
        1187353796428800.0,
        129060195264000.0,
        10559470521600.0,
        670442572800.0,
        33522128640.0,
        1323241920.0,
        40840800.0,
        960960.0,
        16380.0,
        182.0,
        1.0,
    )

    n = a.shape[0]
    ident = np.eye(n, dtype=a.dtype)
    a_norm = np.linalg.norm(a, ord=np.inf)
    s = max(0, int(np.ceil(np.log2(a_norm / 5.371920351148152))))
    a_scaled = a / (2**s)

    a2 = a_scaled @ a_scaled
    a4 = a2 @ a2
    a6 = a4 @ a2

    u = (
        a_scaled
        @ (
            a6
            @ (
                b[13] * a6
                + b[11] * a4
                + b[9] * a2
                + b[7] * ident
            )
            + b[5] * a6
            + b[3] * a4
            + b[1] * a2
        )
    )
    v = (
        a6
        @ (
            b[12] * a6
            + b[10] * a4
            + b[8] * a2
            + b[6] * ident
        )
        + b[4] * a6
        + b[2] * a4
        + b[0] * a2
    )

    numer = u + v
    denom = -u + v
    result = np.linalg.solve(denom, numer)

    for _ in range(s):
        result = result @ result
    return result


def process_matrix(a: np.ndarray, dt: float) -> np.ndarray:
    """Return the continuous-time process matrix ``Phi``.

    Parameters
    ----------
    a:
        Continuous-time state matrix ``A``.
    dt:
        Discretization interval ``Δt``.
    """

    a = np.asarray(a, dtype=float)
    return _matrix_exponential(a * dt)


def van_loan_discretization(
    a: np.ndarray,
    g: np.ndarray,
    qc: np.ndarray,
    dt: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """Discretise a linear SDE using the Van Loan block exponential.

    Returns the state transition matrix ``Phi`` together with the discrete
    process noise covariance ``Qd``.
    """

    a = np.asarray(a, dtype=float)
    g = np.asarray(g, dtype=float)
    qc = np.asarray(qc, dtype=float)

    block = np.block(
        [
            [-a, g @ qc @ g.T],
            [np.zeros_like(a), a.T],
        ]
    )

    exp_block = _matrix_exponential(block * dt)
    n = a.shape[0]
    phi = exp_block[:n, :n].T  # transpose because block is built with -A.
    qd = phi @ exp_block[:n, n:]
    return phi, qd


def discrete_process_noise(
    a: np.ndarray,
    g: np.ndarray,
    qc: np.ndarray,
    dt: float,
) -> np.ndarray:
    """Compute the discrete-time process noise covariance ``Qd``."""

    phi, qd = van_loan_discretization(a, g, qc, dt)
    # ``phi`` is returned for convenience by ``van_loan_discretization`` but
    # callers sometimes only need ``Qd``.
    return qd


def mean_squared_deviation(
    mean: np.ndarray,
    reference: np.ndarray,
    covariance: np.ndarray,
) -> float:
    """Compute the mean-squared deviation for a Gaussian estimate."""

    mean = np.asarray(mean, dtype=float).reshape(-1)
    reference = np.asarray(reference, dtype=float).reshape(-1)
    covariance = np.asarray(covariance, dtype=float)
    deviation = mean - reference
    return float(np.trace(covariance) + deviation @ deviation)


def diagonalize(a: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return eigenvectors ``V`` and eigenvalues ``Λ`` of ``A``.

    The tuple satisfies ``A = V Λ V⁻¹`` when ``A`` is diagonalisable.
    """

    w, v = np.linalg.eig(a)
    return v, np.diag(w)


def finite_horizon_lqr(
    f: np.ndarray,
    b: np.ndarray,
    q: np.ndarray,
    r: np.ndarray,
    horizon: int,
    *,
    terminal_cost: np.ndarray | None = None,
) -> List[np.ndarray]:
    """Solve a discrete-time finite-horizon LQR problem.

    Returns a list of feedback gain matrices ``K_k`` for ``k = 0 … N-1``.
    """

    f = np.asarray(f, dtype=float)
    b = np.asarray(b, dtype=float)
    q = np.asarray(q, dtype=float)
    r = np.asarray(r, dtype=float)

    p_next = np.asarray(terminal_cost if terminal_cost is not None else q, dtype=float)
    gains: List[np.ndarray] = []

    for _ in range(horizon):
        s = r + b.T @ p_next @ b
        k = np.linalg.solve(s, b.T @ p_next @ f)
        gains.append(k)
        p_next = (
            q
            + f.T
            @ (
                p_next
                - p_next @ b @ np.linalg.solve(s, b.T @ p_next)
            )
            @ f
        )

    gains.reverse()
    return gains


def rk4_convolution(
    phi: Callable[[float], np.ndarray],
    b: np.ndarray,
    u: Callable[[float], np.ndarray],
    dt: float,
) -> np.ndarray:
    """Approximate the inhomogeneous integral using RK4 nodes."""

    k1 = phi(dt) @ (b @ u(0.0))
    k2 = phi(dt / 2.0) @ (b @ u(dt / 2.0))
    k3 = phi(dt / 2.0) @ (b @ u(dt / 2.0))
    k4 = phi(0.0) @ (b @ u(dt))
    return dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0


def huber_irls(
    x: np.ndarray,
    y: np.ndarray,
    *,
    delta: float = 1.0,
    weights: np.ndarray | None = None,
    steps: int = 20,
    tol: float = 1e-9,
) -> np.ndarray:
    """Robust linear regression via Iteratively Reweighted Least Squares."""

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = x.shape[0]

    if weights is None:
        w = np.ones(n)
    else:
        w = np.asarray(weights, dtype=float).copy()
    beta = np.linalg.lstsq(x * np.sqrt(w)[:, None], y * np.sqrt(w), rcond=None)[0]

    for _ in range(steps):
        residual = y - x @ beta
        scale = np.maximum(np.abs(residual), 1e-12)
        w_new = np.minimum(1.0, delta / scale)
        beta_new = np.linalg.lstsq(
            x * np.sqrt(w_new)[:, None], y * np.sqrt(w_new), rcond=None
        )[0]
        if np.linalg.norm(beta_new - beta) < tol:
            beta = beta_new
            break
        beta = beta_new
        w = w_new
    return beta


ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALPHABET_INDEX = {c: i for i, c in enumerate(ALPHABET)}


def caesar_cipher(text: str, shift: int) -> str:
    """Return the Caesar-cipher shift of ``text``."""

    result = []
    mod = len(ALPHABET)
    for ch in text.upper():
        if ch in ALPHABET_INDEX:
            result.append(ALPHABET[(ALPHABET_INDEX[ch] + shift) % mod])
        else:
            result.append(ch)
    return "".join(result)


def digram_counts(text: str) -> dict[str, int]:
    """Count digram frequencies in ``text`` (letters only)."""

    filtered = [ch for ch in text.upper() if ch in ALPHABET_INDEX]
    counts: dict[str, int] = {}
    for i in range(len(filtered) - 1):
        digram = filtered[i] + filtered[i + 1]
        counts[digram] = counts.get(digram, 0) + 1
    return counts
