import sys
from pathlib import Path

import pytest

# Ensure the project root is importable when tests are executed from a different cwd.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from door_walk_residue import door_walk_residue


def test_forward_walk_returns_first_non_zero_remainder():
    assert door_walk_residue(10, 2) == 1


def test_backward_walk_handles_decrementing_modulus():
    assert door_walk_residue(10, 5, direction="backward") == 2


def test_backward_walk_with_negative_modulus_respects_python_modulo():
    assert door_walk_residue(7, 1, direction="backward") == -1


def test_invalid_direction_raises_value_error():
    with pytest.raises(ValueError):
        door_walk_residue(10, 3, direction="sideways")


def test_zero_dividend_raises_value_error():
    with pytest.raises(ValueError):
        door_walk_residue(0, 3)


def test_non_integer_arguments_raise_type_error():
    with pytest.raises(TypeError):
        door_walk_residue(10.0, 3)

    with pytest.raises(TypeError):
        door_walk_residue(10, 3.5)

    with pytest.raises(TypeError):
        door_walk_residue(10, 3, direction=1)  # type: ignore[arg-type]
