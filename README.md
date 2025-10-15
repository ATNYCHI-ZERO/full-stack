# K-Math Psychology Toolkit

Utilities and a simple Streamlit UI for exploring the harmonic text-analysis concepts outlined in the tensegrity and K-Math research notes.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI Demo

Run the module directly to analyze the built-in sample text and export JSON + flashcards:

```bash
python kmath_psych.py
```

## Streamlit App

Launch the interactive console:

```bash
streamlit run app_streamlit.py
```

Paste any passage to generate glyph annotations, harmonic resonance values, JSON output, and CSV flashcards. The app also exposes download buttons for the generated files.
