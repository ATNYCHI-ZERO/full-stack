"""Public API for the :mod:`tri_crown` utility package.

The project historically bundled several loosely related modules covering
linear-systems analysis, Kalman filtering utilities, and a handful of
text/cryptographic helpers.  During a previous edit the package-level
initialiser became corrupted which left the module in a syntax-error
state and prevented imports such as ``import tri_crown.math_process``.

This file restores a minimal but well-defined public surface by
re-exporting the symbols that external code relies on.  The focused
structure keeps backwards compatibility with the annex documentation
while ensuring ``import tri_crown`` works in test environments.
"""

from .math_process import (
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
    huber_irls as annex_huber_irls,
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
    huber_irls as process_huber_irls,
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

# Export a unified ``huber_irls`` symbol that defaults to the annex
# implementation while still keeping both variants available for callers
# that relied on the ``process`` helper previously.
huber_irls = annex_huber_irls

__all__ = [
    "apply_caesar_shift",
    "bigram_probabilities",
    "caesar_cipher",
    "causal_convolution",
    "compose_process_and_wave",
    "diagonalize",
    "digram_counts",
    "discrete_process_noise",
    "discretize_falling_body",
    "features_digest",
    "finite_horizon_lqr",
    "fixed_point_key_binding",
    "fourier_energy_ratios",
    "green_convolution",
    "huber_irls",
    "interrogative_score",
    "kalman_predict",
    "kalman_step",
    "kalman_update",
    "math_salt",
    "matrix_exponential",
    "mean_squared_deviation",
    "modal_coordinates",
    "process_huber_irls",
    "process_matrix",
    "process_noise_white_acc",
    "reverse_letters",
    "riccati_gain",
    "rk4_convolution",
    "van_loan_discretization",
]

# ``process_huber_irls`` is intentionally exported under its own name so
# that legacy callers can access that specific implementation if needed.
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

