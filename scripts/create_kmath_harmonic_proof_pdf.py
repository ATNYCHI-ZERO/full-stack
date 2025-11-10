"""Generate the P ≠ NP Kharnita Mathematics proof PDF without external deps."""
from __future__ import annotations

from pathlib import Path
from textwrap import wrap

PDF_PATH = Path(__file__).resolve().parents[1] / "docs" / "P_Not_EQ_NP_KMath_Validation_Paper.pdf"
PAGE_WIDTH = 612  # 8.5 inches * 72 points
PAGE_HEIGHT = 792  # 11 inches * 72 points
MARGIN = 72
FONT_SIZE = 12
LEADING = 14

FULL_TEXT = """
A Formal Proof of P ≠ NP via Recursive and Harmonic Algebraic Operators in Kharnita and Crown Omega Mathematics

Author: Brendon Joseph Kelly
Affiliation: Kharnita Mathematics Research Laboratory; K Systems and Securities
Date: October 7, 2025

Abstract
We present a formal proof of P ≠ NP utilizing recursive, temporal, and harmonic algebraic structures internal to the Kharnita Mathematics and Crown Omega frameworks. By transforming canonical NP-complete problems, such as the Boolean Satisfiability Problem (SAT), into recursive operator equations, we analyze the computational resources required for their solution. We demonstrate that for any such problem, the evaluation of its "Harmonic Synthesis Operator" necessitates an operator recursion depth that grows...
"""
# (file contains long body; the script composes a PDF without external deps)

TRANSLATIONS = {
    "∈": "in",
    "≠": "!=",
    "Ω": "Omega",
    "†": "*",
    "𝒦": "K",
    "𝒮": "S",
    "∑": "Sum",
    "≥": ">=",
    "≤": "<=",
    "∃": "Exists",
    "∎": "QED",
    "→": "->",
    "Θ": "Theta",
    "α": "alpha",
    "…": "...",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
    "’": "'",
    "‘": "'",
    "\u2003": " ",
}


def _normalise(text: str) -> str:
    for original, replacement in TRANSLATIONS.items():
        text = text.replace(original, replacement)
    return text


def _escape(text: str) -> str:
    """Escape text for use inside a PDF string literal."""
    text = _normalise(text)
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_text_stream() -> bytes:
    lines: list[str] = []
    for paragraph in FULL_TEXT.split("\n\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        normalised = _normalise(paragraph)
        for wrapped in wrap(normalised, width=86):
            lines.append(wrapped)
        lines.append("")

    text_ops = [
        "BT",
        f"/F1 {FONT_SIZE} Tf",
        f"{MARGIN} {PAGE_HEIGHT - MARGIN} Td",
    ]

    for line in lines:
        if line:
            text_ops.append(f"({_escape(line)}) Tj")
        text_ops.append(f"0 -{LEADING} Td")

    text_ops.append("ET")
    return "\n".join(text_ops).encode("latin1")


def build_pdf(destination: Path = PDF_PATH) -> Path:
    """Build the PDF at *destination* and return the path."""
    text_stream = _build_text_stream()

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] "
            "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        ).format(w=PAGE_WIDTH, h=PAGE_HEIGHT).encode("latin1"),
        (
            "4 0 obj << /Length {length} >> stream\n"
        ).format(length=len(text_stream)).encode("latin1")
        + text_stream
        + b"\nendstream\nendobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]

    header = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"
    byte_chunks = [header]
    offsets = [0]
    current_len = len(header)

    for obj in objects:
        offsets.append(current_len)
        byte_chunks.append(obj)
        current_len += len(obj)

    xref_start = current_len
    xref_lines = ["xref", "0 6", "0000000000 65535 f "]
    for offset in offsets[1:]:
        xref_lines.append(f"{offset:010} 00000 n ")

    xref = ("\n".join(xref_lines) + "\n").encode("latin1")
    trailer = (
        "trailer << /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".format(
            start=xref_start
        ).encode("latin1")
    )

    pdf_bytes = b"".join(byte_chunks) + xref + trailer
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(pdf_bytes)
    return destination


if __name__ == "__main__":
    path = build_pdf()
    print(f"PDF written to {path}")
