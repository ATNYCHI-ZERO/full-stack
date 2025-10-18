#!/usr/bin/env python3
"""CROWN Ω° Prototype v0.1 – all-in-one demo."""

import math
import zlib
from typing import Tuple

import numpy as np
from Cryptodome.Hash import SHA3_256

THETA = math.pi / 3  # phase twist


def _phase_vec(n: int) -> np.ndarray:
    """Vector of complex phases e^{iθ·pc(i)} cached per length."""
    phases = np.empty(n, dtype=np.complex128)
    for i in range(n):
        phases[i] = np.exp(1j * THETA * bin(i).count("1"))
    return phases


def _hadamard(vec: np.ndarray) -> np.ndarray:
    """Classic Walsh–Hadamard transform."""
    out = vec.astype(np.complex128, copy=True)
    h = 1
    n = out.shape[0]
    while h < n:
        step = h * 2
        for i in range(0, n, step):
            a = out[i : i + h]
            b = out[i + h : i + step]
            out[i : i + h] = a + b
            out[i + h : i + step] = a - b
        h = step
    return out / math.sqrt(n)


def omega_star(vec):
    """Ω★ transform: phase twist around Walsh–Hadamard."""
    arr = np.asarray(vec, dtype=np.complex128)
    n = arr.shape[0]
    if n & (n - 1):
        raise ValueError("Ω★ requires power-of-two length")
    phases = _phase_vec(n)
    return _hadamard(phases * arr) * phases.conj()


def delta_star(u, v):
    """Δ★(u, v) = Ω★(u) + v."""
    return omega_star(u) + np.asarray(v, dtype=np.complex128)


def _compressed_size(data: bytes) -> int:
    return len(zlib.compress(data))


def crown_complexity(signal) -> float:
    raw = np.asarray(signal).tobytes()
    spec = omega_star(signal).tobytes()
    return _compressed_size(spec) / _compressed_size(raw)


def crown_zeta_star(s: complex, n_terms: int = 2 ** 12):
    def parity(idx: int) -> int:
        return 1 if bin(idx).count("1") % 2 == 0 else -1

    total = 0.0 + 0.0j
    for n in range(1, n_terms):
        total += parity(n) * (n ** (-s))
    return total


def _toy_ring_lwe_key() -> Tuple[Tuple[np.ndarray, np.ndarray], np.ndarray]:
    q, dim = 3329, 256
    a = np.random.randint(0, q, dim)
    secret = np.random.randint(0, q, dim)
    error = np.random.randint(-4, 5, dim)
    public = (a * secret + error) % q
    return (a, public), secret


def _toy_ring_lwe_shared(public: Tuple[np.ndarray, np.ndarray], secret: np.ndarray) -> np.ndarray:
    a, public_vec = public
    return (public_vec * secret) % 3329


def _pad_to_power_of_two(arr: np.ndarray) -> np.ndarray:
    n = 1 << (arr.size - 1).bit_length()
    if arr.size == n:
        return arr.astype(float)
    padded = np.zeros(n, dtype=float)
    padded[: arr.size] = arr
    return padded


def crown_session_key() -> bytes:
    pub_a, sec_a = _toy_ring_lwe_key()
    pub_b, sec_b = _toy_ring_lwe_key()
    shared_ab = _toy_ring_lwe_shared(pub_b, sec_a)
    shared_ba = _toy_ring_lwe_shared(pub_a, sec_b)
    if not np.array_equal(shared_ab, shared_ba):
        raise RuntimeError("toy Ring-LWE failed to agree on shared secret")
    pad_ab = _pad_to_power_of_two(shared_ab)
    pad_ba = _pad_to_power_of_two(shared_ba)
    mixed = delta_star(pad_ab, pad_ba).real
    digest = SHA3_256.new(omega_star(mixed).tobytes())
    return digest.digest()


def _self_test() -> None:
    vec = np.random.randn(8)
    back = omega_star(omega_star(vec))
    print("Ω★ self-inverse:", np.allclose(vec, back))
    print("Complexity ratio:", round(crown_complexity(vec), 3))
    print("ζ★(2):", crown_zeta_star(2))
    key = crown_session_key()
    print("Session key (SHA3-256, hex):", key.hex())


if __name__ == "__main__":
    _self_test()
