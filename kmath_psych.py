"""Utilities for analyzing text with K-Math inspired harmonic metadata."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Iterable, Sequence

import re


class KMath:
    """Minimal implementation of the recursive folding routine."""

    def recursive_fold(self, data: object, depth: int = 4) -> dict[str, object]:
        h = hashlib.sha3_512(str(data).encode()).hexdigest()
        vec: list[float] = []
        for i in range(0, 64, 8):
            v = int(h[i : i + 8], 16) / 1e10
            x = v
            for _ in range(depth):
                try:
                    x = math.log(abs(x) + 1) * math.sin(x ** math.pi)
                except Exception:
                    x = math.sin(x)
            vec.append(x)
        return {"hex": h, "vec": vec}

    def get_harmonic_resonance(self, data_hash: str) -> float:
        resonance = (int(data_hash[:8], 16) % 1000) + 432.0
        return float(resonance)


class ChronoMath:
    """Derive a simple temporal scalar from text."""

    def get_temporal_vector(self, text: str) -> float:
        return time.time() + (abs(hash(text)) % 31_536_000)


GLYPH_DICT = {
    "memory": "🧠",
    "anxiety": "⚠",
    "reward": "★",
    "punishment": "✖",
    "sleep": "🌙",
    "attention": "🔎",
    "learning": "⚙",
    "motivation": "🔥",
    "depression": "☁",
}


def extract_glyphs(text: str) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for word, glyph in GLYPH_DICT.items():
        if re.search(r"\\b" + re.escape(word) + r"\\b", text, flags=re.IGNORECASE):
            found.append({"word": word, "glyph": glyph})
    return found


def analyze_text_block(text_block: str) -> list[dict[str, object]]:
    km = KMath()
    cm = ChronoMath()
    sentences = re.split(r"(?<=[.!?])\\s+", text_block.strip())
    nodes: list[dict[str, object]] = []
    for sentence in sentences:
        if not sentence.strip():
            continue
        glyphs = extract_glyphs(sentence)
        fold = km.recursive_fold(sentence)
        resonance = km.get_harmonic_resonance(fold["hex"])
        temporal_vector = cm.get_temporal_vector(sentence)
        nodes.append(
            {
                "sentence": sentence.strip(),
                "glyphs": glyphs,
                "fold_hex": fold["hex"],
                "fold_vec": fold["vec"],
                "resonance_Hz": resonance,
                "temporal_vector": temporal_vector,
            }
        )
    return nodes


def export_json(nodes: Sequence[dict[str, object]], outpath: str | Path = "kmath_psych_output.json") -> Path:
    path = Path(outpath)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(list(nodes), handle, indent=2, ensure_ascii=False)
    print("Exported:", path)
    return path


def export_flashcards(nodes: Iterable[dict[str, object]], csv_out: str | Path = "flashcards.csv") -> Path:
    path = Path(csv_out)
    rows: list[tuple[str, str]] = []
    for node in nodes:
        front = node.get("sentence", "")[:120]
        glyphs = ",".join(g["glyph"] for g in node.get("glyphs", []))
        resonance = node.get("resonance_Hz", 0.0)
        back = f"Glyphs: {glyphs} | Resonance: {resonance:.2f}Hz"
        rows.append((front, back))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Front", "Back"])
        writer.writerows(rows)
    print("Flashcards CSV:", path)
    return path


def csv_to_pdf(csv_file: str | Path, pdf_file: str | Path) -> Path:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    csv_path = Path(csv_file)
    pdf_path = Path(pdf_file)
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter
    y = height - 40
    with csv_path.open(encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for front, back in reader:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(40, y, front)
            y -= 12
            c.setFont("Helvetica", 9)
            c.drawString(40, y, back)
            y -= 30
            if y < 60:
                c.showPage()
                y = height - 40
    c.save()
    print("PDF created:", pdf_path)
    return pdf_path


def _demo_sample() -> str:
    return (
        "Memory consolidation depends on sleep. "
        "High anxiety increases attentional bias to threat. "
        "Rewards strengthen learning via dopamine pathways."
    )


if __name__ == "__main__":
    sample = _demo_sample()
    nodes = analyze_text_block(sample)
    export_json(nodes)
    export_flashcards(nodes)
    print(json.dumps(nodes, indent=2, ensure_ascii=False))
