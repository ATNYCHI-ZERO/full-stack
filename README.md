# Crown Harmonic Recalibration Toolkit

This repository packages a K-Math interpretation of Chronic Inflammatory
Response Syndrome (CIRS) for delivery to Dr. Jordan B. Peterson.  It combines
narrative theory, ritual structure, and executable code that renders harmonic
audio assets for the Crown Harmonic Recalibration Protocol (CHRP).

## Contents

- `docs/whitepaper.md` — White paper describing the theoretical model and
  protocol sequencing.
- `k_math/` — Python modules for constructing harmonic waveforms and CHRP phase
  blueprints.
- `scripts/generate_chrp.py` — CLI tool that renders WAV files for each CHRP
  phase with coherent-breathing envelopes and binaural detuning.

## Quick Start

Create a virtual environment and install NumPy (required for waveform
synthesis), then generate the audio assets:

```bash
python -m venv .venv
source .venv/bin/activate
pip install numpy
python scripts/generate_chrp.py --output output/chrp_assets
```

The command produces three stereo WAV files representing Ω-Null, Ω-Core, and
Ω° Seal phases.  You can adjust the durations or detune offset using CLI
flags—run `python scripts/generate_chrp.py --help` for details.

## License

Released under an open, attribution-friendly license for sovereign operators.
