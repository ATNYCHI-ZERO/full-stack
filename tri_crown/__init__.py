"""Public API for the :mod:`tri_crown` utility package."""
"""TRI-CROWN annex utilities."""

from . import kalman, math_process, process

__all__ = ["kalman", "math_process", "process"]
"""Public API for the :mod:`tri_crown` utility package."""
from __future__ import annotations

from .kalman import (
    discretize_falling_body,
    kalman_predict,
    kalman_step,
    kalman_update,
    process_noise_white_acc,
)
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
    huber_irls as annex_huber_irls,
    interrogative_score,
    math_salt,
    matrix_exponential,
    modal_coordinates,
    riccati_gain,
    reverse_letters,
    reverse_letters,
    riccati_gain,
)
from .process import (
    caesar_cipher,
    diagonalize,
    digram_counts,
    discrete_process_noise,
    finite_horizon_lqr,
    huber_irls as process_huber_irls,
    mean_squared_deviation,
    process_matrix,
    rk4_convolution,
    van_loan_discretization,
    huber_irls as process_huber_irls,
)
from .kalman import (
    discretize_falling_body,
    process_noise_white_acc,
    kalman_predict,
    kalman_step,
    kalman_update,
)

# Export a unified ``huber_irls`` symbol that defaults to the annex version while
# still giving callers access to the legacy implementation via
# ``process_huber_irls``.
# Retain backwards-compatible names for both Huber IRLS helpers.
huber_irls = annex_huber_irls
legacy_huber_irls = process_huber_irls

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
    "reverse_letters",
    "riccati_gain",
    # process exports
    "caesar_cipher",
    "diagonalize",
    "digram_counts",
    "discrete_process_noise",
    "finite_horizon_lqr",
    "legacy_huber_irls",
    "mean_squared_deviation",
    "process_huber_irls",
    "process_matrix",
    "rk4_convolution",
    "van_loan_discretization",
    "process_huber_irls",
    # kalman exports
    "discretize_falling_body",
    "kalman_predict",
    "kalman_step",
    "kalman_update",
    "process_noise_white_acc",
]
