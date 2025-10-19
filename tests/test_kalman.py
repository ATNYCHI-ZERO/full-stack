import numpy as np
import pytest

from tri_crown import kalman


def test_discretize_falling_body_zero_drag_matches_constant_accel():
    dt = 0.1
    f, b = kalman.discretize_falling_body(dt, beta=0.0)
    expected_f = np.array([[1.0, dt], [0.0, 1.0]])
    expected_b = np.array([[0.5 * dt * dt], [dt]])
    assert np.allclose(f, expected_f)
    assert np.allclose(b, expected_b)


def test_discretize_falling_body_drag_relationships():
    dt = 0.05
    beta = 0.3
    f, b = kalman.discretize_falling_body(dt, beta=beta)
    eb = np.exp(-beta * dt)
    a = (1.0 - eb) / beta
    assert np.isclose(f[1, 1], eb)
    assert np.isclose(f[0, 1], a)
    assert np.isclose(f[0, 0], 1.0 + a)
    expected_b = np.array([[dt - a], [1.0 - eb]]) / beta
    assert np.allclose(b, expected_b)


def test_discretize_falling_body_rejects_negative_drag():
    with pytest.raises(ValueError):
        kalman.discretize_falling_body(0.1, beta=-0.1)


def test_process_noise_white_acc_matches_closed_form():
    dt = 0.2
    q = 3.0
    q_matrix = kalman.process_noise_white_acc(dt, q)
    expected = q * np.array([[dt ** 3 / 3.0, dt * dt / 2.0], [dt * dt / 2.0, dt]])
    assert np.allclose(q_matrix, expected)


def test_kalman_predict_and_update_are_consistent():
    dt = 0.1
    f = np.array([[1.0, dt], [0.0, 1.0]])
    q = 0.01 * np.eye(2)
    b = np.array([[0.5 * dt * dt], [dt]])
    u = np.array([1.0])
    x0 = np.array([0.0, 0.0])
    p0 = np.eye(2)

    x_pred, p_pred = kalman.kalman_predict(x0, p0, f, q, b=b, u=u)
    assert x_pred.shape == (2,)
    assert p_pred.shape == (2, 2)

    h = np.array([[1.0, 0.0]])
    r = np.array([[0.05]])
    z = np.array([0.8])

    x_upd, p_upd, k_gain, innovation = kalman.kalman_update(x_pred, p_pred, z, h, r)
    assert np.allclose(innovation, z - h @ x_pred)
    assert np.allclose(x_upd, x_pred + k_gain @ innovation)
    identity = np.eye(2)
    expected_p = (identity - k_gain @ h) @ p_pred @ (identity - k_gain @ h).T + k_gain @ r @ k_gain.T
    assert np.allclose(p_upd, expected_p)


def test_kalman_step_matches_predict_then_update():
    dt = 0.05
    f = np.array([[1.0, dt], [0.0, 1.0]])
    q = 0.02 * np.eye(2)
    x0 = np.array([0.2, -0.1])
    p0 = np.diag([0.5, 0.3])
    z = np.array([0.15])
    h = np.array([[1.0, 0.0]])
    r = np.array([[0.03]])

    x_pred, p_pred = kalman.kalman_predict(x0, p0, f, q)
    direct = kalman.kalman_update(x_pred, p_pred, z, h, r)
    stepped = kalman.kalman_step(x0, p0, z, f, h, q, r)
    assert all(np.allclose(a, b) for a, b in zip(direct, stepped))
