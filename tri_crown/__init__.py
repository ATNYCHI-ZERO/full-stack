"""TRI-CROWN Annexes utilities.

This package collects linear-systems, robust statistics, and
cryptographic helpers referenced in the TRI-CROWN annex specification.
"""

from .process import (
    van_loan_discretization,
    process_matrix,
    discrete_process_noise,
    mean_squared_deviation,
    diagonalize,
    finite_horizon_lqr,
    rk4_convolution,
    huber_irls,
    caesar_cipher,
    digram_counts,
)
from .kalman import (
    discretize_falling_body,
    process_noise_white_acc,
    kalman_predict,
    kalman_update,
    kalman_step,
)

__all__ = [
    "van_loan_discretization",
    "process_matrix",
    "discrete_process_noise",
    "mean_squared_deviation",
    "diagonalize",
    "finite_horizon_lqr",
    "rk4_convolution",
    "huber_irls",
    "caesar_cipher",
    "digram_counts",
    "discretize_falling_body",
    "process_noise_white_acc",
    "kalman_predict",
    "kalman_update",
    "kalman_step",
]
