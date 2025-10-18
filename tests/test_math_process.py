import numpy as np

from tri_crown.math_process import (
    apply_caesar_shift,
    bigram_probabilities,
    causal_convolution,
    compose_process_and_wave,
    fixed_point_key_binding,
    fourier_energy_ratios,
    green_convolution,
    huber_irls,
    interrogative_score,
    math_salt,
    matrix_exponential,
    modal_coordinates,
    riccati_gain,
)


def test_matrix_exponential_matches_series_for_small_dt():
    A = np.array([[0.0, 1.0], [-2.0, -3.0]])
    dt = 0.1
    exp_direct = matrix_exponential(A, dt)
    # Simple sanity: e^{A dt} should map identity initial condition close to Taylor expansion.
    series = np.eye(2) + A * dt + (A @ A) * (dt**2) / 2
    assert np.allclose(exp_direct, series, atol=5e-2)


def test_green_convolution_shapes_and_progression():
    A = np.array([[0.0, 1.0], [0.0, 0.0]])
    B = np.eye(2)
    controls = np.ones((3, 2))
    disc = green_convolution(A, B, controls, dt=0.2)
    assert disc.phi.shape == (2, 2)
    assert disc.gamma.shape == (2, 2)
    assert disc.state_trajectory.shape == (4, 2)


def test_modal_coordinates_returns_eigendecomposition():
    A = np.array([[2.0, 0.0], [0.0, 3.0]])
    V, Lambda = modal_coordinates(A)
    reconstructed = V @ Lambda @ np.linalg.inv(V)
    assert np.allclose(A, reconstructed)


def test_riccati_gain_produces_stabilising_feedback():
    A = np.array([[1.0, 1.0], [0.0, 1.0]])
    B = np.array([[0.0], [1.0]])
    Q = np.eye(2)
    R = np.array([[1.0]])
    K, P = riccati_gain(A, B, Q, R)
    closed_loop = A - B @ K
    eigenvalues = np.linalg.eigvals(closed_loop)
    assert np.all(np.abs(eigenvalues) < 1.0 + 1e-6)
    assert np.all(np.linalg.eigvals(P) > 0)


def test_compose_process_and_wave_block_structure():
    phi = np.eye(2)
    wave = np.eye(3)
    comp = compose_process_and_wave(phi, wave)
    assert comp.shape == (5, 5)
    assert np.allclose(comp[:2, :2], phi)
    assert np.allclose(comp[2:, 2:], wave)
    assert np.allclose(comp[:2, 2:], 0)


def test_causal_convolution_matches_manual_accumulation():
    phi = np.eye(2)
    gamma = np.eye(2)
    controls = np.array([[1.0, 0.0], [0.0, 1.0]])
    result = causal_convolution(phi, gamma, controls)
    assert np.allclose(result[0], [1.0, 0.0])
    assert np.allclose(result[1], [1.0, 1.0])


def test_fourier_energy_ratios_invariant_to_scale():
    signal = np.array([0.0, 1.0, 0.0, -1.0])
    ratios = fourier_energy_ratios(signal)
    ratios_scaled = fourier_energy_ratios(signal * 3)
    assert np.allclose(ratios, ratios_scaled)


def test_text_features_basic_properties():
    text = "Hello world how are you?"
    shifted = apply_caesar_shift(text, 5)
    assert shifted.lower() != text.lower()
    bigrams = bigram_probabilities(text)
    assert abs(sum(bigrams.values()) - 1.0) < 1e-6
    assert interrogative_score(text) >= 1


def test_huber_irls_recovers_mean_for_gaussian_data():
    rng = np.random.default_rng(42)
    X = np.ones((20, 1))
    y = 3.0 + 0.1 * rng.standard_normal(20)
    result = huber_irls(X, y, delta=1.0)
    assert abs(result.coefficients[0] - 3.0) < 1e-1
    assert result.scale >= 0


def test_fixed_point_and_math_salt_are_deterministic():
    seed = b"seed"
    key1, commit1 = fixed_point_key_binding(seed, features=[b"a", b"b"])
    key2, commit2 = fixed_point_key_binding(seed, features=[b"a", b"b"])
    assert key1 == key2
    assert commit1 == commit2

    phi = np.eye(2)
    gamma = np.eye(2)
    wave = np.eye(2)
    salt1, dig1 = math_salt(phi, gamma, wave, "Hello")
    salt2, dig2 = math_salt(phi, gamma, wave, "Hello")
    assert salt1 == salt2
    assert np.allclose(dig1.fourier, dig2.fourier)
    assert dig1.bigrams == dig2.bigrams
