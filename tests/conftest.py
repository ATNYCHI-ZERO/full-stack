import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
"""Pytest configuration ensuring local packages resolve during collection."""
from __future__ import annotations

"""Test configuration that ensures the repository root is importable."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

