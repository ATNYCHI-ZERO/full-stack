import numpy as np

from tri_crown import process


def test_process_matrix_matches_analytic_for_upper_triangular():
    a = np.array([[0.0, 1.0], [0.0, -0.2]])
    dt = 0.1
    phi = process.process_matrix(a, dt)
    expected = np.array(
        [
            [1.0, (1 - np.exp(-0.2 * dt)) / 0.2],
            [0.0, np.exp(-0.2 * dt)],
        ]
    )
    assert np.allclose(phi, expected)


def test_van_loan_discretization_properties():
    a = np.array([[0.0, 1.0], [0.0, 0.0]])
    g = np.array([[0.0], [1.0]])
    qc = np.array([[1.0]])
    dt = 0.2
    phi, qd = process.van_loan_discretization(a, g, qc, dt)
    expected_phi = process.process_matrix(-a.T, dt)
    assert np.allclose(phi, expected_phi)
    assert np.allclose(process.discrete_process_noise(a, g, qc, dt), qd)


def test_discrete_process_noise_returns_covariance_only():
    a = np.array([[0.0]])
    g = np.array([[1.0]])
    qc = np.array([[2.0]])
    dt = 0.5
    qd = process.discrete_process_noise(a, g, qc, dt)
    assert qd.shape == (1, 1)


def test_mean_squared_deviation_combines_bias_and_variance():
    mean = np.array([1.0, -1.0])
    reference = np.zeros(2)
    covariance = np.eye(2) * 0.5
    msd = process.mean_squared_deviation(mean, reference, covariance)
    assert np.isclose(msd, 0.5 * 2 + 2.0)


def test_diagonalize_reconstructs_matrix():
    a = np.array([[2.0, 1.0], [0.0, 3.0]])
    v, lam = process.diagonalize(a)
    reconstructed = v @ lam @ np.linalg.inv(v)
    assert np.allclose(a, reconstructed)


def test_finite_horizon_lqr_returns_gain_sequence():
    f = np.array([[1.0, 1.0], [0.0, 1.0]])
    b = np.array([[0.0], [1.0]])
    q = np.eye(2)
    r = np.array([[1.0]])
    gains = process.finite_horizon_lqr(f, b, q, r, horizon=5)
    assert len(gains) == 5
    closed_loop = f - b @ gains[0]
    eigs = np.linalg.eigvals(closed_loop)
    assert np.all(np.abs(eigs) < 1.1)


def test_rk4_convolution_matches_scalar_integral():
    def phi(t: float) -> np.ndarray:
        return np.array([[np.exp(-t)]])

    b = np.array([[1.0]])

    def u(t: float) -> np.ndarray:
        return np.array([t])

    dt = 0.1
    result = process.rk4_convolution(phi, b, u, dt)
    expected = (dt - 1.0) + np.exp(-dt)
    assert np.allclose(result, np.array([[expected]]), atol=1e-4)


def test_process_huber_irls_is_robust_to_outliers():
    x = np.column_stack([np.ones(20), np.linspace(0, 1, 20)])
    true_beta = np.array([1.0, 2.0])
    y = x @ true_beta
    y[::5] += 10.0  # inject outliers
    beta = process.huber_irls(x, y, delta=1.0)
    assert np.allclose(beta, true_beta, atol=0.5)


def test_caesar_cipher_and_digram_counts():
    text = "Attack at dawn"
    shifted = process.caesar_cipher(text, 3)
    assert "DWWDFN" in shifted
    counts = process.digram_counts("ABCA")
    assert counts == {"AB": 1, "BC": 1, "CA": 1}
