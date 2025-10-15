"""TRI-CROWN math/process annex utilities.

This package exposes high-level helpers that implement the analytical
components described in the TRI-CROWN 1.1 Math/Process Annex.  They are
separated from the cryptographic core so that the existing KEM+AEAD
construction is untouched while still allowing callers to derive the
additional context binding material defined by the annex.
"""

from .math_process import (
    matrix_exponential,
    green_convolution,
    riccati_gain,
    modal_coordinates,
    compose_process_and_wave,
    causal_convolution,
    fourier_energy_ratios,
    bigram_probabilities,
    interrogative_score,
    apply_caesar_shift,
    reverse_letters,
    huber_irls,
    fixed_point_key_binding,
    features_digest,
    math_salt,
)

__all__ = [
    "matrix_exponential",
    "green_convolution",
    "riccati_gain",
    "modal_coordinates",
    "compose_process_and_wave",
    "causal_convolution",
    "fourier_energy_ratios",
    "bigram_probabilities",
    "interrogative_score",
    "apply_caesar_shift",
    "reverse_letters",
    "huber_irls",
    "fixed_point_key_binding",
    "features_digest",
    "math_salt",
]
