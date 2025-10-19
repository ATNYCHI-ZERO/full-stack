"""Synthetic intent classification model used by the POC.

The real system would fuse multiple biometric and telemetry signals to
estimate operator intent.  Here we train a lightweight logistic regression
model on synthetic data so that the end-to-end flow can be exercised without
external datasets.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


FEATURE_NAMES = [
    "EEG_alpha",
    "EEG_beta",
    "HRV",
    "GSR_rate",
    "Voice_stress",
    "Typing_speed",
]


@dataclass
class IntentModel:
    """Stub intent model with deterministic synthetic training."""

    random_state: int = 1337

    def __post_init__(self) -> None:
        self._scaler = StandardScaler()
        self._clf = LogisticRegression(random_state=self.random_state)
        self._is_trained = False

    def train(self, n: int = 1000) -> None:
        """Train on a synthetic dataset with separable benign/malicious modes."""

        benign_mean = np.array([0.6, 0.4, 0.7, 0.2, 0.3, 0.5])
        malicious_mean = np.array([0.3, 0.7, 0.3, 0.6, 0.8, 0.2])
        benign = np.random.default_rng(self.random_state).normal(benign_mean, 0.08, size=(n // 2, len(FEATURE_NAMES)))
        malicious = np.random.default_rng(self.random_state + 1).normal(malicious_mean, 0.1, size=(n // 2, len(FEATURE_NAMES)))
        X = np.vstack([benign, malicious])
        y = np.concatenate([np.ones(len(benign)), np.zeros(len(malicious))])

        Xs = self._scaler.fit_transform(X)
        self._clf.fit(Xs, y)
        self._is_trained = True

    def predict(self, features: np.ndarray) -> Tuple[float, Dict[str, float]]:
        """Predict intent score and provide a simple explanation vector."""

        if not self._is_trained:
            raise RuntimeError("IntentModel must be trained before prediction")

        arr = np.asarray(features, dtype=float).reshape(1, -1)
        Xs = self._scaler.transform(arr)
        score = float(self._clf.predict_proba(Xs)[0, 1])
        contributions = self._feature_contributions(Xs[0])
        return score, contributions

    def _feature_contributions(self, normalized_features: np.ndarray) -> Dict[str, float]:
        weights = self._clf.coef_[0]
        raw = weights * normalized_features
        return {name: float(val) for name, val in zip(FEATURE_NAMES, raw)}
