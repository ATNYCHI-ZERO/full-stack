"""Policy evaluation logic for the intent-auth POC."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Policy:
    policy_id: str = "default"
    allow_threshold: float = 0.90
    stepup_threshold: float = 0.75
    deny_threshold: float = 0.45

    def __post_init__(self) -> None:
        if not (0.0 <= self.deny_threshold <= self.stepup_threshold <= self.allow_threshold <= 1.0):
            raise ValueError("Policy thresholds must satisfy 0 <= deny <= stepup <= allow <= 1")


def decide(score: float, policy: Policy) -> str:
    """Return ALLOW/STEPUP/DENY for the provided score."""

    if score >= policy.allow_threshold:
        return "ALLOW"
    if score >= policy.stepup_threshold:
        return "STEPUP"
    return "DENY"
