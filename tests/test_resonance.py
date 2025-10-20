import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from resonance import detect_resonances, resonance_match


def test_resonance_match_returns_index_pairs(capsys):
    data = [1, 1, 2, 3, 3, 3]

    result = resonance_match(data)

    assert result == [(0, 1), (3, 4), (4, 5)]
    captured = capsys.readouterr()
    assert "[(0, 1), (3, 4), (4, 5)]" in captured.out


def test_detect_resonances_aggregates_sequences():
    sequences = ([0, 0, 1], [2, 3, 4], [5, 5, 5])

    expected = [[(0, 1)], [], [(0, 1), (1, 2)]]
    assert detect_resonances(sequences) == expected
