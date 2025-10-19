"""Signed audit logging for the intent-auth POC."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


class AuditLog:
    """Very small append-only audit log backed by JSON."""

    def __init__(self, signer: Ed25519PrivateKey, path: str | Path = "audit_log.json") -> None:
        self._signer = signer
        self._path = Path(path)
        self._records: List[Dict[str, Any]] = []
        if self._path.exists():
            try:
                self._records = json.loads(self._path.read_text("utf-8"))
            except json.JSONDecodeError:
                # Start fresh if the existing file is corrupted.
                self._records = []

    @property
    def signer_public_key(self) -> bytes:
        return self._signer.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    def log(self, event: Dict[str, Any]) -> None:
        enriched = dict(event)
        enriched.setdefault("ts", int(time.time()))
        payload = json.dumps(enriched, sort_keys=True).encode("utf-8")
        signature = self._signer.sign(payload)
        record = {
            "event": enriched,
            "signature": base64.b64encode(signature).decode("ascii"),
        }
        self._records.append(record)
        self._path.write_text(json.dumps(self._records, indent=2), encoding="utf-8")

    def records(self) -> List[Dict[str, Any]]:
        return list(self._records)
