"""Synthetic dataset generator for the intent model."""
from __future__ import annotations

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "EEG_alpha",
    "EEG_beta",
    "HRV",
    "GSR_rate",
    "Voice_stress",
    "Typing_speed",
]


def generate_dataset(n: int = 2000, seed: int = 0, output_path: str = "intent_dataset.csv") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    benign = rng.normal([0.6, 0.4, 0.7, 0.2, 0.3, 0.5], 0.1, size=(n // 2, len(FEATURE_COLUMNS)))
    malicious = rng.normal([0.3, 0.7, 0.3, 0.6, 0.8, 0.2], 0.12, size=(n // 2, len(FEATURE_COLUMNS)))
    X = np.vstack([benign, malicious])
    y = np.concatenate([np.ones(len(benign)), np.zeros(len(malicious))])
    df = pd.DataFrame(X, columns=FEATURE_COLUMNS)
    df["intent"] = y
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    frame = generate_dataset()
    print("Dataset saved:", frame.shape)
