"""Convenience exports for the TRI-CROWN annex helpers."""

from __future__ import annotations

from .math_process import (
    FeatureDigests,
    ProcessDiscretisation,
    apply_caesar_shift,
    bigram_probabilities,
    causal_convolution,
    compose_process_and_wave,
    features_digest,
    fixed_point_key_binding,
    fourier_energy_ratios,
    green_convolution,
    huber_irls,
    interrogative_score,
    math_salt,
    matrix_exponential,
    modal_coordinates,
    riccati_gain,
    reverse_letters,
)
from .process import (
    caesar_cipher,
    diagonalize,
    digram_counts,
    discrete_process_noise,
    finite_horizon_lqr,
    huber_irls as legacy_huber_irls,
    mean_squared_deviation,
    process_matrix,
    rk4_convolution,
    van_loan_discretization,
)
from .kalman import (
    discretize_falling_body,
    kalman_predict,
    kalman_step,
    kalman_update,
    process_noise_white_acc,
)

__all__ = [
    # math_process exports
    "FeatureDigests",
    "ProcessDiscretisation",
    "apply_caesar_shift",
    "bigram_probabilities",
    "causal_convolution",
    "compose_process_and_wave",
    "features_digest",
    "fixed_point_key_binding",
    "fourier_energy_ratios",
    "green_convolution",
    "huber_irls",
    "interrogative_score",
    "math_salt",
    "matrix_exponential",
    "modal_coordinates",
    "riccati_gain",
    "reverse_letters",
    # process exports
    "caesar_cipher",
    "diagonalize",
    "digram_counts",
    "discrete_process_noise",
    "finite_horizon_lqr",
    "legacy_huber_irls",
    "mean_squared_deviation",
    "process_matrix",
    "rk4_convolution",
    "van_loan_discretization",
    # kalman exports
    "discretize_falling_body",
    "kalman_predict",
    "kalman_step",
    "kalman_update",
    "process_noise_white_acc",
]

