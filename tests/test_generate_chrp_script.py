from types import SimpleNamespace

import numpy as np
import pytest

import scripts.generate_chrp as gen


def test_duration_argument_validates_positive():
    assert gen._duration_argument("2") == 120.0


def test_duration_argument_rejects_non_positive():
    with pytest.raises(Exception):
        gen._duration_argument("0")


def test_generate_chrp_main_invokes_render_and_write(monkeypatch, tmp_path, capsys):
    phases = [SimpleNamespace(name="Ω Null"), SimpleNamespace(name="Ω Core"), SimpleNamespace(name="Ω° Seal")]
    monkeypatch.setattr(gen, "chrp_phases", lambda: phases)

    rendered = []

    def fake_render(phase, duration_s, sample_rate, detune_hz):
        rendered.append((phase.name, duration_s, sample_rate, detune_hz))
        return np.ones((4, 2)) * duration_s

    monkeypatch.setattr(gen, "_render_phase", fake_render)

    written = []

    def fake_write(path, data, sample_rate):
        written.append((path, data.shape, sample_rate))

    monkeypatch.setattr(gen, "_write_wav", fake_write)

    args = SimpleNamespace(
        sample_rate=1000,
        detune=1.0,
        durations=[1.0, 2.0, 3.0],
        output=tmp_path,
    )
    monkeypatch.setattr(gen, "parse_args", lambda argv=None: args)

    gen.main()
    captured = capsys.readouterr().out

    assert len(rendered) == 3
    assert len(written) == 3
    assert any("chrp_omega_null.wav" in str(entry[0]) for entry in written)
    assert "Generated CHRP assets" in captured
