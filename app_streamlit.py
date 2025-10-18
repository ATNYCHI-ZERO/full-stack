"""Streamlit interface for the K-Math psychology analyzer."""

from __future__ import annotations

import streamlit as st

from kmath_psych import analyze_text_block, export_flashcards, export_json

st.title("K-Math Psychology Console")
st.write(
    "Paste a paragraph or chapter to generate harmonic metadata, glyph tags, "
    "and exportable study materials."
)

text_input = st.text_area("Paste chapter or paragraph here")

if st.button("Analyze"):
    if not text_input.strip():
        st.warning("Please provide text to analyze.")
    else:
        nodes = analyze_text_block(text_input)
        st.write(nodes)
        json_path = export_json(nodes)
        csv_path = export_flashcards(nodes)
        st.success("Analysis complete. Files exported.")
        st.download_button(
            "Download JSON",
            data=json_path.read_bytes(),
            file_name=json_path.name,
            mime="application/json",
        )
        st.download_button(
            "Download Flashcards CSV",
            data=csv_path.read_bytes(),
            file_name=csv_path.name,
            mime="text/csv",
        )
