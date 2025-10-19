import math

import numpy as np
import pytest

import crown_omega_core as coc


def test_omega_matches_manual_butterfly():
    vec = np.array([1.0, 2.0, 3.0, 4.0])
    expected = np.array([5.0, 2.0, 1.5, 0.5])
    assert np.allclose(coc.omega(vec), expected)
    with pytest.raises(ValueError):
        coc.omega([1.0, 2.0, 3.0])


def _manual_walsh_parity(n: int) -> int:
    return 1 if bin(n).count("1") % 2 == 0 else -1


def test_delta_combines_transformed_and_direct_components():
    u = [1.0, 0.0, -1.0, 0.0]
    v = [0.5, -0.5, 0.5, -0.5]
    delta = coc.delta(u, v)
    assert np.allclose(delta, coc.omega(u) + np.array(v))


def test_harmonic_integral_matches_trapezoidal_reference():
    signal = np.sin(np.linspace(0, 2 * math.pi, 8, endpoint=False))
    dx = 0.25
    result = coc.harmonic_integral(signal, dx=dx)
    omega_sig = coc.omega(signal)
    trapezoid = np.cumsum((omega_sig[1:] + omega_sig[:-1]) / 2.0) * dx
    assert np.allclose(result, trapezoid)


def test_crown_convolve_matches_fft_reference():
    x = np.array([1.0, 2.0, 3.0])
    y = np.array([0.5, -0.5, 1.0])
    result = coc.crown_convolve(x, y)
    n = 1 << (max(len(x), len(y)) - 1).bit_length()
    x_pad = np.pad(x, (0, n - len(x)))
    y_pad = np.pad(y, (0, n - len(y)))
    expected = np.real(np.fft.ifft(np.fft.fft(coc.omega(x_pad)) * np.fft.fft(y_pad)))[: len(x)]
    assert np.allclose(result, expected)


def test_crown_zeta_matches_manual_sum_for_small_n():
    s = 2 + 0j
    n = 64
    direct = sum(_manual_walsh_parity(k) * (k ** (-s)) for k in range(1, n))
    assert complex(coc.crown_zeta(s, N=n)) == pytest.approx(direct)


def test_kolmogorov_proxy_and_complexity_behaviour():
    payload = b"ABCD" * 8
    proxy = coc.kolmogorov_proxy(payload)
    assert isinstance(proxy, int)
    ratio = coc.crown_complexity([1, 2, 3, 4])
    assert ratio > 0


def test_crown_key_exchange_is_deterministic():
    alice = b"ALICE"
    bob = b"BOB-KEY"
    session1 = coc.crown_key_exchange(alice, bob)
    session2 = coc.crown_key_exchange(alice, bob)
    assert session1 == session2
    assert len(session1) == 32
    empty = coc.crown_key_exchange(b"", b"")
    assert len(empty) == 32


def test_crown_ns_symbolic_handles_optional_dependency():
    if coc.sp is None:
        with pytest.raises(RuntimeError):
            coc.crown_ns_symbolic()
    else:
        expr = coc.crown_ns_symbolic()
        assert coc.sp.Eq == type(expr)
