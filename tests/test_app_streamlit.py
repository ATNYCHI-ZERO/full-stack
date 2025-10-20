import importlib
import sys
import types
from pathlib import Path

import pytest


class StreamlitStub(types.SimpleNamespace):
    def __init__(self, *, text: str, button_presses: list[bool]):
        super().__init__()
        self._text = text
        self._presses = iter(button_presses)
        self.events: list[tuple[str, object]] = []
        self.download_payloads: list[dict[str, object]] = []

    def title(self, label: str) -> None:
        self.events.append(("title", label))

    def write(self, message):
        self.events.append(("write", message))

    def text_area(self, label: str) -> str:
        self.events.append(("text_area", label))
        return self._text

    def button(self, label: str) -> bool:
        self.events.append(("button", label))
        return next(self._presses, False)

    def warning(self, message: str) -> None:
        self.events.append(("warning", message))

    def success(self, message: str) -> None:
        self.events.append(("success", message))

    def download_button(self, label: str, *, data: bytes, file_name: str, mime: str):
        self.events.append(("download_button", label))
        self.download_payloads.append({"label": label, "file_name": file_name, "mime": mime, "data": data})


def _load_app(stub: StreamlitStub, kmath_module: types.SimpleNamespace):
    sys.modules["streamlit"] = stub
    sys.modules["kmath_psych"] = kmath_module
    if "app_streamlit" in sys.modules:
        del sys.modules["app_streamlit"]
    module = importlib.import_module("app_streamlit")
    return module


def _cleanup_modules():
    for name in ("app_streamlit", "streamlit", "kmath_psych"):
        sys.modules.pop(name, None)


def test_streamlit_module_warns_on_empty_submission(tmp_path: Path):
    stub = StreamlitStub(text="   ", button_presses=[True])
    kmath_stub = types.SimpleNamespace(
        analyze_text_block=lambda text: (_ for _ in ()).throw(RuntimeError("should not run")),
        export_json=lambda nodes: tmp_path / "unused.json",
        export_flashcards=lambda nodes: tmp_path / "unused.csv",
    )
    try:
        _load_app(stub, kmath_stub)
    finally:
        _cleanup_modules()
    warning_events = [event for event in stub.events if event[0] == "warning"]
    assert warning_events and "Please provide" in warning_events[0][1]


class _KMStub(types.SimpleNamespace):
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.analyzed: list[str] = []
        super().__init__(
            analyze_text_block=self._analyze,
            export_json=self._export_json,
            export_flashcards=self._export_csv,
        )

    def _analyze(self, text: str):
        self.analyzed.append(text)
        return [{"sentence": text, "glyphs": []}]

    def _export_json(self, nodes):
        path = self.tmp_path / "out.json"
        path.write_text("{}", encoding="utf-8")
        return path

    def _export_csv(self, nodes):
        path = self.tmp_path / "out.csv"
        path.write_text("front,back\n", encoding="utf-8")
        return path


def test_streamlit_module_runs_full_analysis(tmp_path: Path):
    stub = StreamlitStub(text="Signal", button_presses=[True])
    kmath_stub = _KMStub(tmp_path)
    try:
        module = _load_app(stub, kmath_stub)
    finally:
        _cleanup_modules()
    assert kmath_stub.analyzed == ["Signal"]
    success_messages = [event for event in stub.events if event[0] == "success"]
    assert success_messages and "Analysis complete" in success_messages[0][1]
    labels = [payload["label"] for payload in stub.download_payloads]
    assert labels == ["Download JSON", "Download Flashcards CSV"]
    assert module.text_input == "Signal"
