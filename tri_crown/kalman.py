"""Kalman filtering utilities for the TRI-CROWN annexes."""
from __future__ import annotations

from typing import Tuple

import numpy as np


def discretize_falling_body(dt: float, beta: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
    """Return the discrete state transition and input matrices.

    ``beta`` denotes the linear drag coefficient (``β ≥ 0``).  When ``β`` is
    zero the dynamics reduce to constant-acceleration motion.
    """

    if beta < 0.0:
        raise ValueError("beta must be non-negative")

    if beta == 0.0:
        f = np.array([[1.0, dt], [0.0, 1.0]])
        b = np.array([[0.5 * dt * dt], [dt]])
        return f, b

    eb = np.exp(-beta * dt)
    a = (1.0 - eb) / beta
    f = np.array([[1.0 + a, a], [0.0, eb]])
    b = np.array([[dt - a], [1.0 - eb]]) / beta
    return f, b


def process_noise_white_acc(dt: float, q: float) -> np.ndarray:
    """Discretise white-acceleration spectral density ``q``."""

    dt2 = dt * dt
    dt3 = dt2 * dt
    return q * np.array([[dt3 / 3.0, dt2 / 2.0], [dt2 / 2.0, dt]])


def kalman_predict(
    x: np.ndarray,
    p: np.ndarray,
    f: np.ndarray,
    q: np.ndarray,
    b: np.ndarray | None = None,
    u: np.ndarray | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Kalman predict step for linear Gaussian systems."""

    x = np.asarray(x, dtype=float)
    p = np.asarray(p, dtype=float)
    f = np.asarray(f, dtype=float)
    q = np.asarray(q, dtype=float)

    x_pred = f @ x
    if b is not None and u is not None:
        x_pred = x_pred + np.asarray(b, dtype=float) @ np.asarray(u, dtype=float)
    p_pred = f @ p @ f.T + q
    return x_pred, p_pred


def kalman_update(
    x_pred: np.ndarray,
    p_pred: np.ndarray,
    z: np.ndarray,
    h: np.ndarray,
    r: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Kalman update step returning state, covariance, gain, and innovation."""

    h = np.asarray(h, dtype=float)
    r = np.asarray(r, dtype=float)

    innovation = np.asarray(z, dtype=float) - h @ x_pred
    s = h @ p_pred @ h.T + r
    k = p_pred @ h.T @ np.linalg.inv(s)
    x = x_pred + k @ innovation
    identity = np.eye(p_pred.shape[0])
    p = (identity - k @ h) @ p_pred @ (identity - k @ h).T + k @ r @ k.T
    return x, p, k, innovation


def kalman_step(
    x: np.ndarray,
    p: np.ndarray,
    z: np.ndarray,
    f: np.ndarray,
    h: np.ndarray,
    q: np.ndarray,
    r: np.ndarray,
    *,
    b: np.ndarray | None = None,
    u: np.ndarray | None = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Single predict-update cycle of the Kalman filter."""

    x_pred, p_pred = kalman_predict(x, p, f, q, b=b, u=u)
    return kalman_update(x_pred, p_pred, z, h, r)
