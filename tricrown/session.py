"""High level TRI-CROWN 2.0 handshake and record layer helpers.

The goal of this module is to provide an easily auditable reference skeleton
that mirrors the suite specification.  It does not attempt to be a production
ready TLS alternative; instead it illustrates how the different components fit
together and gives developers a jumping-off point for integrating hardened PQC
libraries.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from hmac import compare_digest
from typing import Iterable, List, Sequence

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import crypto
from .crypto import (
    HKDFParams,
    commit_tag,
    derive_message_key,
    derive_nonce,
    mix_shared_secrets,
    transcript_hash,
)
from .pq import StubKEM, StubSignatureKeypair, random_stub_kem, random_stub_signature

try:  # pragma: no cover - optional dependency
    from nacl import bindings as nacl_bindings
except Exception:  # pragma: no cover - fallback when PyNaCl is unavailable
    nacl_bindings = None


def _json_dumps(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_audit_salt(messages: Iterable[bytes]) -> bytes:
    """Derive the ``s_math`` auditing salt described in the annex.

    The real system would fold in spectral features and state space analysis of
    implementation telemetry.  For the reference code we approximate that idea
    with a collection of deterministic statistics over the transcript.  The
    function intentionally produces a stable output so that transcript hashes
    remain reproducible during testing.
    """

    import math

    stats: List[float] = []
    for idx, message in enumerate(messages):
        length = len(message)
        entropy_est = sum(message.count(byte) for byte in range(256)) / (length or 1)
        stats.append(float(length))
        stats.append(entropy_est + idx)
        stats.append(math.sin(length / (idx + 1 or 1)))

    accumulator = bytearray()
    for value in stats:
        scaled = int(value * (1 << 20)) & 0xFFFFFFFFFFFFFFFF
        accumulator.extend(scaled.to_bytes(8, "big"))

    from hashlib import sha3_256

    return sha3_256(bytes(accumulator)).digest()


@dataclass
class Chains:
    rk: bytes
    ck_s: bytes
    ck_r: bytes
    k_commit: bytes


@dataclass
class TriCrownParty:
    """Represents one side of the TRI-CROWN handshake."""

    role: str
    kem_ml: StubKEM = field(default_factory=lambda: random_stub_kem("ML-KEM-stub"))
    kem_mce: StubKEM = field(default_factory=lambda: random_stub_kem("McEliece-stub"))
    signature: StubSignatureKeypair = field(default_factory=random_stub_signature)
    encapsulate_back: bool = True

    def __post_init__(self) -> None:
        self.x25519_private = x25519.X25519PrivateKey.generate()
        self.x25519_public = self.x25519_private.public_key().public_bytes(
            Encoding.Raw, PublicFormat.Raw
        )

    def _hello_payload(self) -> dict:
        return {
            "role": self.role,
            "kem_ml": self.kem_ml.public_key_bytes().hex(),
            "kem_mce": self.kem_mce.public_key_bytes().hex(),
            "x25519": self.x25519_public.hex(),
            "sig_alg": self.signature.name,
            "sig_pk": self.signature.public_key.hex(),
        }


@dataclass
class AEADBackend:
    """Abstracts the two AEAD options required by the suite."""

    name: str

    def nonce_length(self) -> int:
        return 24 if "XChaCha20" in self.name else 12

    def encrypt(self, key: bytes, nonce: bytes, data: bytes, aad: bytes) -> bytes:
        if self.name == "AES-256-GCM-SIV":
            aead = AESGCM(key)
            return aead.encrypt(nonce, data, aad)
        if self.name == "XChaCha20-Poly1305":
            if nacl_bindings is None:
                raise RuntimeError("PyNaCl is required for XChaCha20-Poly1305 support")
            return nacl_bindings.crypto_aead_xchacha20poly1305_ietf_encrypt(data, aad, nonce, key)
        raise ValueError(f"Unsupported AEAD suite: {self.name}")

    def decrypt(self, key: bytes, nonce: bytes, data: bytes, aad: bytes) -> bytes:
        if self.name == "AES-256-GCM-SIV":
            aead = AESGCM(key)
            return aead.decrypt(nonce, data, aad)
        if self.name == "XChaCha20-Poly1305":
            if nacl_bindings is None:
                raise RuntimeError("PyNaCl is required for XChaCha20-Poly1305 support")
            return nacl_bindings.crypto_aead_xchacha20poly1305_ietf_decrypt(None, data, aad, nonce, key)
        raise ValueError(f"Unsupported AEAD suite: {self.name}")


@dataclass
class Record:
    sequence: int
    nonce: bytes
    ciphertext: bytes
    commitment: bytes
    aad: bytes


@dataclass
class TriCrownSession:
    """Holds the derived secrets and provides record layer helpers."""

    role: str
    session_id: bytes
    transcript: bytes
    chains: Chains
    aead_backend: AEADBackend
    refresh_interval_messages: int = 64
    refresh_interval_seconds: int = 300
    last_refresh_at: float = field(default_factory=lambda: time.time())
    sent_messages: int = 0
    received_messages: int = 0

    def seal(self, plaintext: bytes, *, aad: bytes = b"") -> Record:
        sequence = self.sent_messages
        nonce_len = self.aead_backend.nonce_length()
        current_ck = self.chains.ck_s
        nonce = derive_nonce(current_ck, sequence=sequence, length=nonce_len)
        message_key, next_ck = derive_message_key(current_ck, sequence=sequence)
        self.chains.ck_s = next_ck
        ciphertext = self.aead_backend.encrypt(message_key, nonce, plaintext, aad)
        commitment = commit_tag(
            self.chains.k_commit,
            session_id=self.session_id,
            sequence=sequence,
            nonce=nonce,
            aad=aad,
            ciphertext=ciphertext,
        )
        self.sent_messages += 1
        return Record(sequence=sequence, nonce=nonce, ciphertext=ciphertext, commitment=commitment, aad=aad)

    def open(self, record: Record) -> bytes:
        if record.sequence != self.received_messages:
            raise ValueError("out-of-order record")
        current_ck = self.chains.ck_r
        sequence = record.sequence
        expected_commit = commit_tag(
            self.chains.k_commit,
            session_id=self.session_id,
            sequence=sequence,
            nonce=record.nonce,
            aad=record.aad,
            ciphertext=record.ciphertext,
        )
        if not compare_digest(expected_commit, record.commitment):
            raise ValueError("commitment mismatch")
        message_key, next_ck = derive_message_key(current_ck, sequence=sequence)
        plaintext = self.aead_backend.decrypt(message_key, record.nonce, record.ciphertext, record.aad)
        self.chains.ck_r = next_ck
        self.received_messages += 1
        return plaintext

    def needs_refresh(self) -> bool:
        if self.sent_messages >= self.refresh_interval_messages:
            return True
        if time.time() - self.last_refresh_at >= self.refresh_interval_seconds:
            return True
        return False

    def update_after_refresh(self) -> None:
        self.sent_messages = 0
        self.received_messages = 0
        self.last_refresh_at = time.time()

    def rekey(self, *, new_secrets: Sequence[bytes], transcript: bytes | None = None) -> None:
        th = transcript or self.transcript
        mix_input = [self.chains.rk] + list(new_secrets)
        mix = mix_shared_secrets(transcript=th, shared_secrets=mix_input)
        material = crypto.hkdf_expand(mix, params=HKDFParams(info=b"TRICROWN refresh" + self.role.encode(), length=128))
        rk = material[:32]
        ck_a = material[32:64]
        ck_b = material[64:96]
        k_commit = material[96:128]
        if self.role == "client":
            ck_s, ck_r = ck_a, ck_b
        else:
            ck_s, ck_r = ck_b, ck_a
        self.chains = Chains(rk=rk, ck_s=ck_s, ck_r=ck_r, k_commit=k_commit)
        self.update_after_refresh()


@dataclass
class HandshakeResult:
    """Container for the outcome of a completed handshake."""

    session: TriCrownSession
    transcript: bytes
    shared_secrets: Sequence[bytes]


def perform_handshake(client: TriCrownParty, server: TriCrownParty, *, aead: str = "AES-256-GCM-SIV") -> tuple[HandshakeResult, HandshakeResult]:
    """Execute the reference handshake and return fully initialised sessions."""

    session_id = os.urandom(16)
    messages: List[bytes] = []

    client_hello = client._hello_payload()
    server_hello = server._hello_payload()
    messages.append(_json_dumps({"client_hello": client_hello}))
    messages.append(_json_dumps({"server_hello": server_hello}))

    # shared secrets from the client's encapsulation step
    ct_ml_c, ss_ml_c = client.kem_ml.encapsulate(bytes.fromhex(server_hello["kem_ml"]))
    ct_mce_c, ss_mce_c = client.kem_mce.encapsulate(bytes.fromhex(server_hello["kem_mce"]))
    ss_x = client.x25519_private.exchange(x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(server_hello["x25519"])))

    client_enc = {
        "ct_ml_c": ct_ml_c.hex(),
        "ct_mce_c": ct_mce_c.hex(),
    }
    messages.append(_json_dumps({"client_encaps": client_enc}))

    # server decapsulates and optionally reciprocates with its own encapsulations
    ss_ml_c_server = server.kem_ml.decapsulate(ct_ml_c)
    ss_mce_c_server = server.kem_mce.decapsulate(ct_mce_c)
    ss_x_server = server.x25519_private.exchange(x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(client_hello["x25519"])))

    if server.encapsulate_back:
        ct_ml_s, ss_ml_s = server.kem_ml.encapsulate(bytes.fromhex(client_hello["kem_ml"]))
        ct_mce_s, ss_mce_s = server.kem_mce.encapsulate(bytes.fromhex(client_hello["kem_mce"]))
        server_enc = {
            "ct_ml_s": ct_ml_s.hex(),
            "ct_mce_s": ct_mce_s.hex(),
        }
        messages.append(_json_dumps({"server_encaps": server_enc}))
    else:
        ss_ml_s = ss_mce_s = b""
        server_enc = None

    # Authentication step: sign the current transcript hash
    th2 = transcript_hash(messages)
    client_sig = client.signature.sign(th2)
    server_sig = server.signature.sign(th2)
    if not StubSignatureKeypair.verify(bytes.fromhex(client_hello["sig_pk"]), th2, client_sig):
        raise ValueError("client signature self-check failed")
    if not StubSignatureKeypair.verify(bytes.fromhex(server_hello["sig_pk"]), th2, server_sig):
        raise ValueError("server signature self-check failed")
    messages.append(_json_dumps({"client_sig": client_sig.hex()}))
    messages.append(_json_dumps({"server_sig": server_sig.hex()}))

    th_final = transcript_hash(messages)
    s_math = compute_audit_salt(messages)

    # Each side collects secrets in the same order
    ss_order_client: List[bytes] = [ss_ml_c, ss_mce_c, ss_x]
    ss_order_server: List[bytes] = [ss_ml_c_server, ss_mce_c_server, ss_x_server]
    if server_enc is not None:
        ss_order_client.extend([ss_ml_s, ss_mce_s])
        ss_order_server.extend([ss_ml_s, ss_mce_s])
    ss_order_client.append(s_math)
    ss_order_server.append(s_math)

    mix_client = mix_shared_secrets(transcript=th_final, shared_secrets=ss_order_client)
    mix_server = mix_shared_secrets(transcript=th_final, shared_secrets=ss_order_server)

    hs_info = b"TRICROWN hs"
    material_client = crypto.hkdf_expand(mix_client, params=HKDFParams(info=hs_info + b"client", length=128))
    material_server = crypto.hkdf_expand(mix_server, params=HKDFParams(info=hs_info + b"server", length=128))

    def split_material(material: bytes, role: str) -> Chains:
        rk = material[:32]
        ck_a = material[32:64]
        ck_b = material[64:96]
        k_commit = material[96:128]
        if role == "client":
            ck_s, ck_r = ck_a, ck_b
        else:
            ck_s, ck_r = ck_b, ck_a
        return Chains(rk=rk, ck_s=ck_s, ck_r=ck_r, k_commit=k_commit)

    chains_client = split_material(material_client, "client")
    chains_server = split_material(material_server, "server")

    aead_backend = AEADBackend(aead)

    client_session = TriCrownSession(
        role="client",
        session_id=session_id,
        transcript=th_final,
        chains=chains_client,
        aead_backend=aead_backend,
    )
    server_session = TriCrownSession(
        role="server",
        session_id=session_id,
        transcript=th_final,
        chains=chains_server,
        aead_backend=aead_backend,
    )

    client_shared = tuple(ss_order_client)
    server_shared = tuple(ss_order_server)

    return (
        HandshakeResult(session=client_session, transcript=th_final, shared_secrets=client_shared),
        HandshakeResult(session=server_session, transcript=th_final, shared_secrets=server_shared),
    )
