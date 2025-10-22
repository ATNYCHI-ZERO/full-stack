"""Deterministic reference helpers for the TRI-CROWN hybrid handshake."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:  # pragma: no cover - optional dependency
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import x25519
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305 as _RealChaCha20Poly1305
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
except Exception:  # pragma: no cover - fallback implementation used in tests
    hashes = None  # type: ignore[assignment]
    x25519 = None  # type: ignore[assignment]
    _RealChaCha20Poly1305 = None  # type: ignore[assignment]
    HKDF = None  # type: ignore[assignment]
    Encoding = None  # type: ignore[assignment]
    PublicFormat = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import oqs
except Exception:  # pragma: no cover - degraded mode
    oqs = None

_HAS_OQS = oqs is not None
_DEFAULT_PQ_ALG = "Kyber768"
_TAG_LEN = hashlib.sha256().digest_size


def _b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def _hkdf(ikm: bytes, *, length: int, info: bytes, salt: Optional[bytes] = None) -> bytes:
    """Portable HKDF implementation using hashlib/hmac primitives."""

    if salt is None:
        salt = b"\x00" * hashlib.sha256().digest_size
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    okm = b""
    previous = b""
    counter = 1
    while len(okm) < length:
        previous = hmac.new(prk, previous + info + bytes([counter]), hashlib.sha256).digest()
        okm += previous
        counter += 1
    return okm[:length]


class _StubX25519PublicKey:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def public_bytes(self, _encoding: object, _format: object) -> bytes:  # pragma: no cover - trivial
        return self._data

    @classmethod
    def from_public_bytes(cls, data: bytes) -> "_StubX25519PublicKey":
        return cls(data)


class _StubX25519PrivateKey:
    def __init__(self, secret: Optional[bytes] = None) -> None:
        self._secret = secret or os.urandom(32)

    @classmethod
    def generate(cls) -> "_StubX25519PrivateKey":
        return cls()

    def public_key(self) -> _StubX25519PublicKey:
        digest = hashlib.sha256(b"tricrown-x25519" + self._secret).digest()
        return _StubX25519PublicKey(digest)

    def exchange(self, peer_public_key: _StubX25519PublicKey) -> bytes:
        peer = peer_public_key.public_bytes(None, None)
        own = self.public_key().public_bytes(None, None)
        if own < peer:
            combined = own + peer
        else:
            combined = peer + own
        return hashlib.sha256(b"tricrown-dh" + combined).digest()


class _ChaCha20Poly1305:
    """Wrapper that falls back to a deterministic stream cipher when unavailable."""

    def __init__(self, key: bytes) -> None:
        if _RealChaCha20Poly1305 is not None:
            self._impl = _RealChaCha20Poly1305(key)
            self._key = b""
        else:  # pragma: no cover - exercised when cryptography is missing
            self._impl = None
            self._key = hashlib.sha256(key).digest()

    def encrypt(self, nonce: bytes, data: bytes, aad: bytes) -> bytes:
        if self._impl is not None:
            return self._impl.encrypt(nonce, data, aad)
        keystream = _hkdf(self._key + nonce, length=len(data), info=b"tricrown-hybrid-aead")
        ciphertext = bytes(a ^ b for a, b in zip(data, keystream))
        tag = hmac.new(self._key, nonce + aad + ciphertext, hashlib.sha256).digest()
        return ciphertext + tag

    def decrypt(self, nonce: bytes, data: bytes, aad: bytes) -> bytes:
        if self._impl is not None:
            return self._impl.decrypt(nonce, data, aad)
        if len(data) < _TAG_LEN:
            raise ValueError("ciphertext too short")
        ciphertext, tag = data[:-_TAG_LEN], data[-_TAG_LEN:]
        expected = hmac.new(self._key, nonce + aad + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, tag):
            raise ValueError("authentication failed")
        keystream = _hkdf(self._key + nonce, length=len(ciphertext), info=b"tricrown-hybrid-aead")
        return bytes(a ^ b for a, b in zip(ciphertext, keystream))


@dataclass
class _CipherState:
    key: bytes
    nonce: int = 0

    def next_nonce(self) -> bytes:
        value = self.nonce
        self.nonce += 1
        return value.to_bytes(12, "big")


@dataclass
class _SessionState:
    rk: bytes
    send: _CipherState
    recv: _CipherState


@dataclass
class _HandshakeState:
    role: str
    transcript: List[bytes] = field(default_factory=list)
    dh_private: Optional[object] = None
    dh_shared_secret: Optional[bytes] = None
    client_pub: Optional[bytes] = None
    server_pub: Optional[bytes] = None
    pq_client: Optional[object] = None
    pq_shared_secret: Optional[bytes] = None
    pq_ciphertext: Optional[bytes] = None

    def record(self, message: Dict[str, str]) -> None:
        canonical = "|".join(f"{k}={message[k]}" for k in sorted(message)).encode("utf-8")
        self.transcript.append(canonical)

    def transcript_bytes(self) -> bytes:
        return b"\n".join(self.transcript)


@dataclass
class TriCrownContext:
    role: str
    enable_pq: bool
    pq_alg: Optional[str]
    handshake: _HandshakeState
    chains: Optional[_SessionState] = None

    def require_session(self) -> _SessionState:
        if self.chains is None:
            raise RuntimeError("session not established")
        return self.chains


def _x25519_private_key() -> object:
    if x25519 is not None:
        return x25519.X25519PrivateKey.generate()
    return _StubX25519PrivateKey.generate()


def _x25519_public_bytes(private: object) -> bytes:
    if x25519 is not None:
        return private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return private.public_key().public_bytes(None, None)  # type: ignore[call-arg]


def _x25519_from_public(data: bytes) -> object:
    if x25519 is not None:
        return x25519.X25519PublicKey.from_public_bytes(data)
    return _StubX25519PublicKey.from_public_bytes(data)


def _x25519_exchange(private: object, peer_public: object) -> bytes:
    return private.exchange(peer_public)  # type: ignore[attr-defined]


def _derive_secrets(shared: bytes, pq_secret: bytes, transcript: bytes) -> bytes:
    info = b"tricrown-hybrid-session"
    material = shared + pq_secret
    if HKDF is not None and hashes is not None:
        hkdf = HKDF(algorithm=hashes.SHA256(), length=96, salt=None, info=info)
        okm = hkdf.derive(material)
    else:
        okm = _hkdf(material, length=96, info=info)
    root_key = okm[64:]
    verifier = hmac.new(root_key, transcript, hashlib.sha256).digest()
    return okm[:32], okm[32:64], root_key, verifier


def ctx_init(role: str, enable_pq: bool = False, *, pq_alg: Optional[str] = None) -> TriCrownContext:
    if role not in {"client", "server"}:
        raise ValueError("role must be 'client' or 'server'")
    negotiated_pq = enable_pq and _HAS_OQS
    if negotiated_pq and pq_alg is None:
        pq_alg = _DEFAULT_PQ_ALG
    handshake = _HandshakeState(role=role)
    if negotiated_pq and role == "client":
        handshake.pq_client = oqs.KeyEncapsulation(pq_alg)
    return TriCrownContext(role=role, enable_pq=negotiated_pq, pq_alg=pq_alg, handshake=handshake)


def client_hello(ctx: TriCrownContext) -> Dict[str, str]:
    if ctx.role != "client":
        raise RuntimeError("client_hello called on non-client context")
    priv = _x25519_private_key()
    ctx.handshake.dh_private = priv
    public = _x25519_public_bytes(priv)
    ctx.handshake.client_pub = public
    message: Dict[str, str] = {"type": "client-hello", "x25519": _b64e(public)}
    if ctx.enable_pq and ctx.handshake.pq_client is not None:
        public_key = ctx.handshake.pq_client.generate_keypair()[0]
        message.update({"pq_alg": ctx.pq_alg or _DEFAULT_PQ_ALG, "pq_pub": _b64e(public_key)})
    ctx.handshake.record(message)
    return message


def server_hello(ctx: TriCrownContext, message: Dict[str, str]) -> Dict[str, str]:
    if ctx.role != "server":
        raise RuntimeError("server_hello called on non-server context")
    if message.get("type") != "client-hello":
        raise ValueError("unexpected message type")
    client_pub = _b64d(message["x25519"])
    ctx.handshake.client_pub = client_pub
    priv = _x25519_private_key()
    ctx.handshake.dh_private = priv
    public = _x25519_public_bytes(priv)
    ctx.handshake.server_pub = public
    client_public_key = _x25519_from_public(client_pub)
    shared = _x25519_exchange(priv, client_public_key)
    ctx.handshake.dh_shared_secret = shared
    response: Dict[str, str] = {"type": "server-hello", "x25519": _b64e(public)}
    if ctx.enable_pq and "pq_alg" in message and oqs is not None:
        kem = oqs.KeyEncapsulation(message["pq_alg"])
        try:
            ciphertext, shared_secret = kem.encapsulate(_b64d(message["pq_pub"]))
        finally:
            with suppress(AttributeError):
                kem.free()
        ctx.handshake.pq_shared_secret = shared_secret
        ctx.handshake.pq_ciphertext = ciphertext
        response.update({"pq_alg": message["pq_alg"], "pq_ct": _b64e(ciphertext)})
    ctx.handshake.record(message)
    ctx.handshake.record(response)
    return response


def client_finish(ctx: TriCrownContext, message: Dict[str, str]) -> Dict[str, str]:
    if ctx.role != "client":
        raise RuntimeError("client_finish called on non-client context")
    if message.get("type") != "server-hello":
        raise ValueError("unexpected message type")
    server_pub = _b64d(message["x25519"])
    ctx.handshake.server_pub = server_pub
    priv = ctx.handshake.dh_private
    if priv is None:
        raise RuntimeError("missing client private key")
    server_public_key = _x25519_from_public(server_pub)
    ctx.handshake.record(message)
    shared = _x25519_exchange(priv, server_public_key)
    ctx.handshake.dh_shared_secret = shared
    pq_secret = b""
    if ctx.enable_pq and ctx.handshake.pq_client is not None and "pq_ct" in message:
        pq_secret = ctx.handshake.pq_client.decapsulate(_b64d(message["pq_ct"]))
        ctx.handshake.pq_shared_secret = pq_secret
    send_key, recv_key, root_key, verifier = _derive_secrets(shared, pq_secret, ctx.handshake.transcript_bytes())
    ctx.chains = _SessionState(
        rk=root_key,
        send=_CipherState(key=send_key),
        recv=_CipherState(key=recv_key),
    )
    if ctx.handshake.pq_client is not None:
        with suppress(AttributeError):
            ctx.handshake.pq_client.free()  # type: ignore[attr-defined]
        ctx.handshake.pq_client = None
    return {"type": "client-finish", "verify": _b64e(verifier)}


def server_finish(ctx: TriCrownContext, message: Dict[str, str]) -> None:
    if ctx.role != "server":
        raise RuntimeError("server_finish called on non-server context")
    if message.get("type") != "client-finish":
        raise ValueError("unexpected message type")
    shared = ctx.handshake.dh_shared_secret
    if shared is None:
        raise RuntimeError("missing DH shared secret")
    pq_secret = ctx.handshake.pq_shared_secret or b""
    send_key, recv_key, root_key, verifier = _derive_secrets(shared, pq_secret, ctx.handshake.transcript_bytes())
    provided = _b64d(message["verify"])
    if not hmac.compare_digest(verifier, provided):
        raise ValueError("handshake verification failed")
    ctx.chains = _SessionState(
        rk=root_key,
        send=_CipherState(key=recv_key if ctx.role == "server" else send_key),
        recv=_CipherState(key=send_key if ctx.role == "server" else recv_key),
    )


def _cipher(key: bytes) -> _ChaCha20Poly1305:
    return _ChaCha20Poly1305(key)


def seal(ctx: TriCrownContext, aad: bytes, plaintext: bytes) -> Dict[str, bytes]:
    session = ctx.require_session()
    cipher = _cipher(session.send.key)
    nonce = session.send.next_nonce()
    ciphertext = cipher.encrypt(nonce, plaintext, aad)
    return {"aad": aad, "nonce": nonce, "ct": ciphertext}


def open_(ctx: TriCrownContext, record: Dict[str, bytes]) -> bytes:
    session = ctx.require_session()
    cipher = _cipher(session.recv.key)
    nonce = record["nonce"]
    aad = record.get("aad", b"")
    ciphertext = record["ct"]
    return cipher.decrypt(nonce, ciphertext, aad)


def rekey(ctx: TriCrownContext) -> None:
    session = ctx.require_session()
    info = b"tricrown-rekey"
    if HKDF is not None and hashes is not None:
        hkdf = HKDF(algorithm=hashes.SHA256(), length=96, salt=None, info=info)
        material = hkdf.derive(session.rk)
    else:
        material = _hkdf(session.rk, length=96, info=info)
    client_send, server_send, new_root = material[:32], material[32:64], material[64:]
    if ctx.role == "client":
        send, recv = client_send, server_send
    else:
        send, recv = server_send, client_send
    ctx.chains = _SessionState(rk=new_root, send=_CipherState(key=send), recv=_CipherState(key=recv))


__all__ = [
    "TriCrownContext",
    "ctx_init",
    "client_hello",
    "server_hello",
    "client_finish",
    "server_finish",
    "seal",
    "open_",
    "rekey",
    "_HAS_OQS",
]
