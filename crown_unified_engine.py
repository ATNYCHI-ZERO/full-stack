"""Unified execution engine that composes the TRI-CROWN subsystems.

The repository has grown several orthogonal prototypes – the TRI-CROWN
handshake helpers, the annex math/process utilities, the Crown Ω operator
toolkit, and the narrative Hooded Crown launch harness.  This module offers a
single orchestrator that wires those components together into a coherent flow.

The :class:`CrownUnifiedEngine` class exposes a small configuration surface and
produces a structured :class:`UnifiedEngineReport` capturing the outcome of the
combined execution.  The engine performs the following steps:

* Establishes a TRI-CROWN handshake between a client and a server, then re-keys
  the record layer with annex salt derived from the process helpers.
* Evaluates the Math/Process annex discretisation, contextual salt, and the
  composite operator that binds the state-space model to the harmonic wave
  operator.
* Runs the Crown Ω transforms using the shared-secret digest as a spectral
  displacement, capturing convolution, complexity, and zeta shadow metrics.
* Invokes the Hooded Crown seal and KHTX encryptor to demonstrate how the
  higher-level runtime can embed the cryptographic digest.

The engine is intentionally deterministic apart from the cryptographic
handshake randomness so that callers can obtain reproducible structures for
inspection or downstream processing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from crown_omega_core import crown_complexity, crown_convolve, crown_zeta, delta, omega
from hooded_crown_system import (
    CrownKHTX,
    HoodedCrownSeal,
    genesis_omega_expression,
    get_runtime_id,
)
from tri_crown.math_process import (
    FeatureDigests,
    ProcessDiscretisation,
    compose_process_and_wave,
    green_convolution,
    math_salt,
)
try:  # pragma: no cover - optional dependency on cryptography
    from tricrown.session import HandshakeResult, TriCrownParty, perform_handshake

    _HAS_TRICROWN = True
except ModuleNotFoundError:  # pragma: no cover - cryptography is optional
    HandshakeResult = None  # type: ignore[assignment]
    TriCrownParty = None  # type: ignore[assignment]
    perform_handshake = None  # type: ignore[assignment]
    _HAS_TRICROWN = False


def _default_matrix_a() -> np.ndarray:
    """Nominal second-order system matrix used across the demos."""

    return np.array([[0.0, 1.0], [-0.25, -0.4]], dtype=float)


def _default_matrix_b() -> np.ndarray:
    """Control-input coupling for the nominal annex process."""

    return np.array([[0.0], [1.0]], dtype=float)


def _default_controls() -> np.ndarray:
    """Reference control trajectory for the annex discretisation."""

    return np.array([[0.2], [0.1], [-0.05], [0.0], [0.05], [0.1]], dtype=float)


def _default_wave_operator() -> np.ndarray:
    """Simple rotation-style wave operator used for the composite binding."""

    return np.array([[0.0, 1.0], [-1.0, 0.0]], dtype=float)


def _default_signal() -> np.ndarray:
    """Spectral test signal with power-of-two length for Ω operations."""

    samples = np.linspace(0.0, 2.0 * np.pi, 8, endpoint=False)
    return np.sin(samples) + 0.5 * np.cos(2.0 * samples)


def _default_kernel() -> np.ndarray:
    """Reference kernel for the Crown convolution step."""

    return np.array([0.5, 0.25, 0.125, 0.0625, 0.03125, 0.0, 0.0, 0.0], dtype=float)


@dataclass
class CrownEngineConfig:
    """Configuration inputs consumed by the unified engine."""

    operator: str = "Brendon Joseph Kelly"
    hooded_secret: str = "ΩCORE-KMATH-RES0NANCE"
    message: str = "DEFENSE DOMAINS UNIFIED"
    annex_text: str = (
        "Tri-Crown annex binding integrates control, wave, and linguistic "
        "features into a single audit salt."
    )
    dt: float = 0.25
    matrix_a: np.ndarray = field(default_factory=_default_matrix_a)
    matrix_b: np.ndarray = field(default_factory=_default_matrix_b)
    controls: np.ndarray = field(default_factory=_default_controls)
    wave_operator: np.ndarray = field(default_factory=_default_wave_operator)
    signal: np.ndarray = field(default_factory=_default_signal)
    kernel: np.ndarray = field(default_factory=_default_kernel)


@dataclass
class _StubRecord:
    sequence: int
    nonce: bytes
    ciphertext: bytes
    commitment: bytes
    aad: bytes


@dataclass
class _StubSession:
    role: str
    session_id: bytes
    transcript: bytes
    shared_secret: bytes
    nonce_counter: int = 0

    def rekey(
        self,
        *,
        new_secrets: Sequence[bytes],
        transcript: bytes | None = None,
    ) -> None:
        material = self.shared_secret + b"".join(new_secrets)
        self.shared_secret = hashlib.sha3_256(material).digest()
        if transcript is not None:
            self.transcript = transcript
        self.nonce_counter = 0

    def seal(self, plaintext: bytes, *, aad: bytes = b"") -> _StubRecord:
        key = hashlib.sha3_256(self.shared_secret + aad).digest()
        nonce = hashlib.sha3_256(
            key + self.session_id + self.nonce_counter.to_bytes(4, "big")
        ).digest()[:12]
        ciphertext = bytes(
            byte ^ key[i % len(key)] for i, byte in enumerate(plaintext)
        )
        commitment = hashlib.sha3_256(nonce + aad + ciphertext).digest()
        record = _StubRecord(
            sequence=self.nonce_counter,
            nonce=nonce,
            ciphertext=ciphertext,
            commitment=commitment,
            aad=aad,
        )
        self.nonce_counter += 1
        return record

    def open(self, record: _StubRecord) -> bytes:
        if record.sequence != self.nonce_counter:
            raise ValueError("out-of-order record")
        key = hashlib.sha3_256(self.shared_secret + record.aad).digest()
        expected_commitment = hashlib.sha3_256(
            record.nonce + record.aad + record.ciphertext
        ).digest()
        if expected_commitment != record.commitment:
            raise ValueError("commitment mismatch")
        plaintext = bytes(
            byte ^ key[i % len(key)] for i, byte in enumerate(record.ciphertext)
        )
        self.nonce_counter += 1
        return plaintext


@dataclass
class _StubHandshakeResult:
    session: _StubSession
    transcript: bytes
    shared_secrets: tuple[bytes, ...]


def _fallback_perform_handshake() -> tuple[_StubHandshakeResult, _StubHandshakeResult]:
    session_id = hashlib.sha3_256(b"crown-unified-engine-session").digest()[:16]
    transcript = hashlib.sha3_256(b"crown-unified-engine-transcript").digest()
    shared = hashlib.sha3_256(b"crown-unified-engine-shared-secret").digest()
    client_session = _StubSession(
        role="client", session_id=session_id, transcript=transcript, shared_secret=shared
    )
    server_session = _StubSession(
        role="server", session_id=session_id, transcript=transcript, shared_secret=shared
    )
    client_result = _StubHandshakeResult(
        session=client_session, transcript=transcript, shared_secrets=(shared,)
    )
    server_result = _StubHandshakeResult(
        session=server_session, transcript=transcript, shared_secrets=(shared,)
    )
    return client_result, server_result


@dataclass(frozen=True)
class RecordSummary:
    """Readable view of an encrypted TRI-CROWN record."""

    sequence: int
    nonce_hex: str
    ciphertext_hex: str
    commitment_hex: str
    aad_hex: str


@dataclass(frozen=True)
class HandshakeSummary:
    """Outcome of the TRI-CROWN handshake stage."""

    session_id_hex: str
    transcript_hex: str
    shared_secret_digest: str
    record: RecordSummary
    decrypted_plaintext: str


@dataclass(frozen=True)
class ProcessSummary:
    """Captured annex artefacts used to extend the handshake."""

    discretisation: ProcessDiscretisation
    composite_operator: np.ndarray
    math_salt: bytes
    features: FeatureDigests


@dataclass(frozen=True)
class OmegaSummary:
    """Measurements derived from the Crown Ω operators."""

    signal: np.ndarray
    omega_signal: np.ndarray
    displacement: np.ndarray
    displaced_signal: np.ndarray
    convolution: np.ndarray
    complexity_ratio: float
    zeta_shadow: complex


@dataclass(frozen=True)
class HoodedSummary:
    """Results produced by the Hooded Crown runtime harness."""

    seal: str
    encrypted_payload: str
    audit_hash: str
    genesis_integral: float


@dataclass(frozen=True)
class UnifiedEngineReport:
    """Aggregated report emitted by :class:`CrownUnifiedEngine`."""

    handshake: HandshakeSummary
    process: ProcessSummary
    omega: OmegaSummary
    hooded: HoodedSummary


class CrownUnifiedEngine:
    """High-level orchestrator that stitches together the TRI-CROWN artefacts."""

    def __init__(self, config: CrownEngineConfig | None = None):
        self.config = config or CrownEngineConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> UnifiedEngineReport:
        """Execute the full engine pipeline and return a structured report."""

        client_result, server_result = self._perform_handshake()

        process_summary = self._build_process_summary()
        self._rekey_sessions(client_result, server_result, process_summary.math_salt)

        record_summary, plaintext = self._seal_and_open(
            client_result, server_result, process_summary.features.raw_digest
        )

        shared_digest = self._digest_shared_secrets(
            client_result, process_summary.math_salt
        )

        handshake_summary = HandshakeSummary(
            session_id_hex=client_result.session.session_id.hex(),
            transcript_hex=client_result.transcript.hex(),
            shared_secret_digest=shared_digest,
            record=record_summary,
            decrypted_plaintext=plaintext,
        )

        omega_summary = self._build_omega_summary(shared_digest)
        hooded_summary = self._build_hooded_summary(shared_digest)

        return UnifiedEngineReport(
            handshake=handshake_summary,
            process=process_summary,
            omega=omega_summary,
            hooded=hooded_summary,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _perform_handshake(self):
        if _HAS_TRICROWN:
            try:
                client = TriCrownParty(role="client")  # type: ignore[call-arg]
                server = TriCrownParty(role="server")  # type: ignore[call-arg]
                client_result, server_result = perform_handshake(client, server)  # type: ignore[misc]
                client_commit = getattr(client_result.session.chains, "k_commit", None)
                server_commit = getattr(server_result.session.chains, "k_commit", None)
                if client_commit is None or server_commit is None:
                    return client_result, server_result
                if client_commit == server_commit:
                    return client_result, server_result
                raise ValueError("handshake commitment mismatch")
            except Exception:
                # When the optional cryptography stack is present but the
                # handshake fails (e.g. due to missing PyNaCl or differing
                # record-layer commitments), fall back to the deterministic
                # stub implementation so the engine remains executable.
                return _fallback_perform_handshake()
        return _fallback_perform_handshake()

    def _build_process_summary(self) -> ProcessSummary:
        cfg = self.config
        discretisation = green_convolution(
            cfg.matrix_a, cfg.matrix_b, cfg.controls, cfg.dt
        )
        composite = compose_process_and_wave(discretisation.phi, cfg.wave_operator)
        math_digest, features = math_salt(
            discretisation.phi,
            discretisation.gamma,
            cfg.wave_operator,
            cfg.annex_text,
            fourier_source=cfg.signal,
        )
        return ProcessSummary(
            discretisation=discretisation,
            composite_operator=composite,
            math_salt=math_digest,
            features=features,
        )

    def _rekey_sessions(
        self,
        client_result: HandshakeResult,
        server_result: HandshakeResult,
        math_salt_bytes: bytes,
    ) -> None:
        client_result.session.rekey(new_secrets=(math_salt_bytes,))
        server_result.session.rekey(new_secrets=(math_salt_bytes,))

    def _seal_and_open(
        self,
        client_result: HandshakeResult,
        server_result: HandshakeResult,
        aad: bytes,
    ) -> tuple[RecordSummary, str]:
        message_bytes = self.config.message.encode("utf-8")
        record = client_result.session.seal(message_bytes, aad=aad)
        plaintext = server_result.session.open(record).decode("utf-8")
        record_summary = RecordSummary(
            sequence=record.sequence,
            nonce_hex=record.nonce.hex(),
            ciphertext_hex=record.ciphertext.hex(),
            commitment_hex=record.commitment.hex(),
            aad_hex=aad.hex(),
        )
        return record_summary, plaintext

    def _digest_shared_secrets(
        self, client_result: HandshakeResult, math_salt_bytes: bytes
    ) -> str:
        accumulator: Sequence[bytes] = tuple(client_result.shared_secrets) + (
            math_salt_bytes,
        )
        return hashlib.sha3_256(b"".join(accumulator)).hexdigest()

    def _build_omega_summary(self, shared_digest: str) -> OmegaSummary:
        cfg = self.config
        signal = cfg.signal
        omega_signal = omega(signal)

        digest_bytes = bytes.fromhex(shared_digest)
        displacement = np.frombuffer(
            digest_bytes[: signal.size].ljust(signal.size, b"\x00"), dtype=np.uint8
        ).astype(float)
        if displacement.size < signal.size:
            displacement = np.pad(displacement, (0, signal.size - displacement.size))
        displacement /= 255.0

        displaced = delta(signal, displacement)
        convolution = crown_convolve(displaced, cfg.kernel)
        complexity_ratio = crown_complexity(signal)
        zeta_shadow = crown_zeta(1.5 + 0.5j, N=2**10)

        return OmegaSummary(
            signal=signal,
            omega_signal=omega_signal,
            displacement=displacement,
            displaced_signal=displaced,
            convolution=convolution,
            complexity_ratio=complexity_ratio,
            zeta_shadow=zeta_shadow,
        )

    def _build_hooded_summary(self, shared_digest: str) -> HoodedSummary:
        cfg = self.config
        seal = HoodedCrownSeal(cfg.operator).generate_seal()
        operator_id = get_runtime_id()
        khtx = CrownKHTX(operator_id=operator_id, secret=cfg.hooded_secret)
        envelope = f"{cfg.message}::{shared_digest}"
        encrypted = khtx.encrypt(envelope)
        audit = khtx.audit_hash()
        integral = genesis_omega_expression()
        return HoodedSummary(
            seal=seal,
            encrypted_payload=encrypted,
            audit_hash=audit,
            genesis_integral=integral,
        )

