"""Crown \u03a9\xb0 Mathematics unified operator framework.

This module provides a reference implementation of the operators and utilities
outlined in the project charter:

* Walsh\u2013Hadamard based self-inverse spectral operator ``omega``.
* Spectral displacement operator ``delta``.
* Harmonic integral utilities defined in the \u03a9-domain.
* Spectral convolution, zeta shadow, and Kolmogorov complexity proxy tools.
* Symbolic Navier\u2013Stokes re-write expressed in the \u03a9 spectral basis.
* Crown key exchange primitive based on \u03a9 mixing and SHA3-256.

The module is intentionally self-contained so it can be executed directly to
run a lightweight self-test suite demonstrating the main capabilities.
"""

from __future__ import annotations

import hashlib
import math
import zlib
from typing import Iterable, Union

import numpy as np
import sympy as sp

ArrayLike = Union[Iterable[float], np.ndarray]


# =============================================================================
# 1. \u03a9  \u2013 SELF-INVERSE WALSH\u2013HADAMARD OPERATOR
# =============================================================================

def _hadamard_numeric(vec: np.ndarray) -> np.ndarray:
    """Return the Walsh\u2013Hadamard transform of ``vec``.

    The implementation follows the classical iterative butterfly structure and
    returns an orthonormal transform by scaling with ``sqrt(n)``.  The
    transform is self-inverse, so ``_hadamard_numeric(_hadamard_numeric(v))``
    yields the original vector.
    """

    h = 1
    n = vec.shape[0]
    out = vec.astype(float).copy()
    while h < n:
        for i in range(0, n, h * 2):
            a = out[i : i + h]
            b = out[i + h : i + 2 * h]
            out[i : i + h] = a + b
            out[i + h : i + 2 * h] = a - b
        h *= 2
    return out / math.sqrt(n)


def omega(vec: ArrayLike) -> np.ndarray:
    """Apply the numeric Walsh\u2013Hadamard transform.

    Parameters
    ----------
    vec:
        One-dimensional iterable whose length is a power of two.  Inputs are
        converted to ``float``.  A ``ValueError`` is raised for invalid lengths.
    """

    arr = np.asarray(list(vec), dtype=float)
    n = arr.shape[0]
    if n == 0 or n & (n - 1):  # n must be a power of two.
        raise ValueError("\u03a9 requires vector length to be a power of two")
    return _hadamard_numeric(arr)


def _omega_symbolic(vec: sp.Matrix) -> sp.Matrix:
    """SymPy variant of the Walsh\u2013Hadamard transform."""

    n = vec.shape[0]
    if n == 0 or n & (n - 1):
        raise ValueError("\u03a9 requires vector length to be a power of two")
    hadamard = sp.Matrix([[1, 1], [1, -1]]) / sp.sqrt(2)
    if n == 2:
        return hadamard * vec
    # For larger symbolic vectors fall back to numeric structure with sympy.
    return sp.Matrix(_hadamard_numeric(np.array(vec, dtype=object)))


# =============================================================================
# 2. \u0394  \u2013 HARMONIC DISPLACEMENT
# =============================================================================

def delta(u: ArrayLike, v: ArrayLike) -> np.ndarray:
    """Spectral-domain displacement ``\u0394(u, v) = \u03a9(u) + v``."""

    return omega(u) + np.asarray(list(v), dtype=float)


# =============================================================================
# 3. HARMONIC INTEGRAL (CUMULATIVE \u03a9-FIELD)
# =============================================================================

def harmonic_integral(signal: ArrayLike, dx: float = 1.0) -> np.ndarray:
    """Approximate the integral of ``signal`` in the \u03a9-domain.

    A simple cumulative trapezoidal rule is applied after transforming the
    signal via ``omega``.  The returned array has length ``len(signal) - 1`` to
    match the trapezoidal integration output.
    """

    sig = np.asarray(list(signal), dtype=float)
    omega_sig = omega(sig)
    if omega_sig.size < 2:
        return np.array([], dtype=float)
    return np.cumsum((omega_sig[1:] + omega_sig[:-1]) / 2.0) * dx


# =============================================================================
# 4. SPECTRAL CONVOLUTION (\u03a9-CORRELATION)
# =============================================================================

def crown_convolve(x: ArrayLike, y: ArrayLike) -> np.ndarray:
    """Convolve ``x`` and ``y`` after mapping ``x`` through ``\u03a9``."""

    x_arr = np.asarray(list(x), dtype=float)
    y_arr = np.asarray(list(y), dtype=float)
    size = max(len(x_arr), len(y_arr))
    n = 1 << (size - 1).bit_length()
    x_pad = np.pad(x_arr, (0, n - len(x_arr)))
    y_pad = np.pad(y_arr, (0, n - len(y_arr)))
    return np.real(np.fft.ifft(np.fft.fft(omega(x_pad)) * np.fft.fft(y_pad)))[: len(x_arr)]


# =============================================================================
# 5. CROWN ZETA SHADOW (\u03a9-SPECTRAL DIRICHLET)
# =============================================================================

def _walsh_parity(n: int) -> int:
    """Return +1 for even Hamming weight, -1 for odd."""

    return 1 if bin(n).count("1") % 2 == 0 else -1


def crown_zeta(s: complex, N: int = 2 ** 14) -> complex:
    """Compute the Crown zeta shadow ``\u03b6_\u03a9``."""

    return sum(_walsh_parity(n) * (n ** (-s)) for n in range(1, N))


# =============================================================================
# 6. COMPLEXITY METRIC (COMPRESSIBILITY)
# =============================================================================

def kolmogorov_proxy(data: bytes) -> int:
    """Length of the zlib-compressed payload as a proxy complexity metric."""

    return len(zlib.compress(data))


def crown_complexity(signal: ArrayLike) -> float:
    """Relative complexity before and after the ``\u03a9`` transform."""

    signal_arr = np.asarray(list(signal), dtype=float)
    raw = signal_arr.tobytes()
    spec = omega(signal_arr).tobytes()
    return kolmogorov_proxy(spec) / kolmogorov_proxy(raw)


# =============================================================================
# 7. CROWN-FORM NAVIER\u2013STOKES (SYMBOLIC)
# =============================================================================

def crown_ns_symbolic() -> sp.Eq:
    """Return a symbolic Navier\u2013Stokes form using \u03a9-domain convection."""

    t, x, y = sp.symbols("t x y")
    u = sp.Function("u")(x, y, t)
    p = sp.Function("p")(x, y, t)
    nu = sp.symbols("nu", positive=True, real=True)

    gradient = sp.Matrix([sp.diff(u, x), sp.diff(u, y)])
    crown_conv_term = _omega_symbolic(gradient)

    laplacian = sp.diff(u, x, 2) + sp.diff(u, y, 2)
    pressure_gradient = sp.Matrix([sp.diff(p, x), sp.diff(p, y)])

    return sp.Eq(sp.diff(u, t) + crown_conv_term, -pressure_gradient + nu * laplacian)


# =============================================================================
# 8. POST-QUANTUM CROWN KEY DERIVATION (CKD-\u03a9)
# =============================================================================

def _sha3_256(data: bytes) -> bytes:
    return hashlib.sha3_256(data).digest()


def _pad_to_power_of_two(vec: np.ndarray) -> np.ndarray:
    n = len(vec)
    target = 1 << (n - 1).bit_length()
    return np.pad(vec, (0, target - n))


def _spectral_bytes(arr: np.ndarray) -> bytes:
    """Convert a Walsh\u2013Hadamard output into a byte string."""

    transformed = omega(arr)
    # Map floating point values into the 0-255 range via modular rounding.
    normalized = np.mod(np.round(transformed), 256).astype(np.uint8)
    return normalized.tobytes()


def crown_key_exchange(A: bytes, B: bytes) -> bytes:
    """Derive a shared key via \u03a9 spectral mixing and SHA3-256."""

    a_vec = np.frombuffer(A, dtype=np.uint8)
    b_vec = np.frombuffer(B, dtype=np.uint8)
    max_len = max(len(a_vec), len(b_vec))
    if max_len == 0:
        return _sha3_256(b"")
    a_pad = _pad_to_power_of_two(a_vec)
    b_pad = _pad_to_power_of_two(b_vec)
    part1 = bytes(x ^ y for x, y in zip(_spectral_bytes(a_pad), b_pad.tobytes()))
    part2 = bytes(x ^ y for x, y in zip(_spectral_bytes(b_pad), a_pad.tobytes()))
    return _sha3_256(part1 + part2)


# =============================================================================
# 9. SELF-TEST SUITE
# =============================================================================

def _selftest() -> None:
    v = np.arange(8, dtype=float)
    assert np.allclose(omega(omega(v)), v), "Omega transform must be involutive"

    c_ratio = crown_complexity(v)
    print(f"Complexity ratio \u03a9/raw: {c_ratio:.3f}")

    z2 = crown_zeta(2 + 0j, 2 ** 12)
    print(f"\u03b6_\u03a9(2) \u2248 {z2:.6f}")

    alice_secret = b"ALICE_KEY_MATERIAL"
    bob_secret = b"BOB_KEY_MATERIAL__"
    session_key = crown_key_exchange(alice_secret, bob_secret)
    print(f"Session Key (hex): {session_key.hex()}")

    print("\nCrown-form Navier\u2013Stokes (symbolic):")
    print(crown_ns_symbolic())


if __name__ == "__main__":  # pragma: no cover - manual verification helper
    _selftest()
