import numpy as np

from tri_crown.math_process import FeatureDigests, features_digest, fixed_point_key_binding


def test_features_digest_collects_textual_and_spectral_components():
    phi = np.eye(2)
    gamma = np.ones((2, 2)) * 0.5
    wave = np.array([[0.0, -1.0], [1.0, 0.0]])
    text = "abba"

    digests = features_digest(phi, gamma, wave, text)
    assert isinstance(digests, FeatureDigests)
    assert digests.fourier.shape[0] == 4
    assert abs(sum(digests.bigrams.values()) - 1.0) < 1e-12
    assert digests.interrogatives == 0
    assert len(digests.raw_digest) == 32


def test_features_digest_changes_with_text_content():
    phi = np.eye(1)
    gamma = np.eye(1)
    wave = np.eye(1)
    text_a = "who are you"
    text_b = "hello world"

    digests_a = features_digest(phi, gamma, wave, text_a)
    digests_b = features_digest(phi, gamma, wave, text_b)
    assert digests_a.raw_digest != digests_b.raw_digest
    assert digests_a.interrogatives > digests_b.interrogatives


def test_fixed_point_key_binding_respects_context_rounds():
    seed = b"seed"
    key_default, commit_default = fixed_point_key_binding(seed, features=[b"x"], rounds=2)
    key_alt, commit_alt = fixed_point_key_binding(seed, features=[b"x"], rounds=4)
    assert key_default != key_alt
    assert commit_default != commit_alt
