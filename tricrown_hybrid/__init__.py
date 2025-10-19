"""TriCrown hybrid handshake and record layer implementation."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from contextlib import suppress
from dataclasses import dataclass
from typing import Dict, Optional

try:  # pragma: no cover - optional dependency
    from cryptography.hazmat.primitives.asymmetric import x25519
except Exception:  # pragma: no cover - fallback implementation used
    x25519 = None

try:  # pragma: no cover - optional dependency
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
except Exception:  # pragma: no cover - fallback values
    class _Placeholder:
        def __init__(self, name: str) -> None:
            self.name = name

        def __repr__(self) -> str:  # pragma: no cover - debug helper
            return f"<placeholder {self.name}>"

    Encoding = type("Encoding", (), {"Raw": _Placeholder("Encoding.Raw")})  # type: ignore[assignment]
    PublicFormat = type("PublicFormat", (), {"Raw": _Placeholder("PublicFormat.Raw")})  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305 as _RealChaCha20Poly1305
except Exception:  # pragma: no cover - fallback implementation used
    _RealChaCha20Poly1305 = None

try:  # pragma: no cover - exercised depending on environment
    import oqs
except Exception:  # pragma: no cover - degraded mode
    oqs = None

_HAS_OQS = oqs is not None
_DEFAULT_PQ_ALG = "Kyber768"
_TAG_LEN = hashlib.sha256().digest_size


class _ChaCha20Poly1305:
    """Wrapper that falls back to a simple stream cipher when unavailable."""

    def __init__(self, key: bytes) -> None:
        if _RealChaCha20Poly1305 is not None:
            self._impl = _RealChaCha20Poly1305(key)
            self._key = b""
        else:  # pragma: no cover - exercised when cryptography is missing
            # Normalise key size for the fallback stream cipher
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
        if not secrets.compare_digest(expected, tag):
            raise ValueError("authentication failed")
        keystream = _hkdf(self._key + nonce, length=len(ciphertext), info=b"tricrown-hybrid-aead")
        return bytes(a ^ b for a, b in zip(ciphertext, keystream))


def _hkdf(ikm: bytes, *, length: int, info: bytes, salt: bytes | None = None) -> bytes:
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


if x25519 is None:  # pragma: no cover - exercised when cryptography is missing
    class _StubX25519PublicKey:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def public_bytes(self, _encoding: object, _format: object) -> bytes:
            return self._data

        @classmethod
        def from_public_bytes(cls, data: bytes) -> "_StubX25519PublicKey":
            return cls(data)

    class _StubX25519PrivateKey:
        def __init__(self, secret: bytes | None = None) -> None:
            self._secret = secret or os.urandom(32)

        @classmethod
        def generate(cls) -> "_StubX25519PrivateKey":
            return cls()

        def public_key(self) -> _StubX25519PublicKey:
            pub = hashlib.sha256(b"tricrown-x25519" + self._secret).digest()
            return _StubX25519PublicKey(pub)

        def exchange(self, peer_public_key: _StubX25519PublicKey) -> bytes:
            peer = peer_public_key.public_bytes(None, None)
            own = self.public_key().public_bytes(None, None)
            if own < peer:
                combined = own + peer
            else:
                combined = peer + own
            return hashlib.sha256(b"tricrown-dh" + combined).digest()

    class _StubX25519Module:
        X25519PrivateKey = _StubX25519PrivateKey
        X25519PublicKey = _StubX25519PublicKey

    x25519 = _StubX25519Module()


def _b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64d(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


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
class _HandshakeCache:
    role: str
    enable_pq: bool
    pq_alg: Optional[str]
    client_pub: Optional[bytes] = None
    server_pub: Optional[bytes] = None
    pq_client: Optional["oqs.KeyEncapsulation"] = None
    pq_ciphertext: Optional[bytes] = None
    pq_shared_secret: Optional[bytes] = None
    dh_private: Optional[x25519.X25519PrivateKey] = None
    dh_shared_secret: Optional[bytes] = None

    def transcript(self) -> bytes:
        parts = [b"tricrown-transcript-v1"]
        if self.client_pub:
            parts.append(self.client_pub)
        if self.server_pub:
            parts.append(self.server_pub)
        if self.enable_pq and self.pq_alg:
            parts.append(self.pq_alg.encode("ascii"))
            if self.pq_ciphertext:
                parts.append(self.pq_ciphertext)
        return b"|".join(parts)


@dataclass
class TriCrownContext:
    role: str
    enable_pq: bool
    pq_alg: Optional[str]
    handshake: _HandshakeCache
    chains: Optional[_SessionState] = None

    def require_session(self) -> _SessionState:
        if self.chains is None:
            raise RuntimeError("handshake not finished")
        return self.chains


def ctx_init(role: str, *, enable_pq: bool = True, pq_alg: str = _DEFAULT_PQ_ALG) -> TriCrownContext:
    if role not in {"client", "server"}:
        raise ValueError("role must be 'client' or 'server'")

    pq_enabled = bool(enable_pq and _HAS_OQS)
    pq_algorithm = pq_alg if pq_enabled else None
    handshake = _HandshakeCache(role=role, enable_pq=pq_enabled, pq_alg=pq_algorithm)
    return TriCrownContext(role=role, enable_pq=pq_enabled, pq_alg=pq_algorithm, handshake=handshake)


def client_hello(ctx: TriCrownContext) -> Dict[str, str]:
    priv = x25519.X25519PrivateKey.generate()
    pub = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    ctx.handshake.client_pub = pub
    ctx.handshake.dh_private = priv

    message: Dict[str, str] = {"type": "client-hello", "x25519": _b64e(pub)}

    if ctx.enable_pq and ctx.pq_alg:
        kem = oqs.KeyEncapsulation(ctx.pq_alg)
        public_key = kem.generate_keypair()
        ctx.handshake.pq_client = kem
        message.update({"pq_alg": ctx.pq_alg, "pq_pub": _b64e(public_key)})
    return message


def server_hello(ctx: TriCrownContext, message: Dict[str, str]) -> Dict[str, str]:
    if message.get("type") != "client-hello":
        raise ValueError("unexpected message type")

    client_pub = _b64d(message["x25519"])
    ctx.handshake.client_pub = client_pub

    priv = x25519.X25519PrivateKey.generate()
    pub = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    ctx.handshake.server_pub = pub
    ctx.handshake.dh_private = priv

    client_public_key = x25519.X25519PublicKey.from_public_bytes(client_pub)
    dh_shared = priv.exchange(client_public_key)
    ctx.handshake.dh_shared_secret = dh_shared

    response: Dict[str, str] = {"type": "server-hello", "x25519": _b64e(pub)}

    if ctx.enable_pq and ctx.pq_alg and "pq_alg" in message:
        kem = oqs.KeyEncapsulation(message["pq_alg"])
        try:
            ciphertext, shared_secret = kem.encapsulate(_b64d(message["pq_pub"]))
        finally:
            with suppress(AttributeError):
                kem.free()
        ctx.handshake.pq_shared_secret = shared_secret
        ctx.handshake.pq_ciphertext = ciphertext
        response.update({
            "pq_alg": message["pq_alg"],
            "pq_ct": _b64e(ciphertext),
        })
    return response


def client_finish(ctx: TriCrownContext, message: Dict[str, str]) -> Dict[str, str]:
    if message.get("type") != "server-hello":
        raise ValueError("unexpected message type")

    server_pub = _b64d(message["x25519"])
    ctx.handshake.server_pub = server_pub

    priv = ctx.handshake.dh_private
    if priv is None:
        raise RuntimeError("missing client private key")
    server_public_key = x25519.X25519PublicKey.from_public_bytes(server_pub)
    dh_shared = priv.exchange(server_public_key)
    ctx.handshake.dh_shared_secret = dh_shared

    pq_secret = b""
    if ctx.enable_pq and ctx.pq_alg and "pq_ct" in message:
        ciphertext = _b64d(message["pq_ct"])
        ctx.handshake.pq_ciphertext = ciphertext
        if ctx.handshake.pq_client:
            pq_secret = ctx.handshake.pq_client.decapsulate(ciphertext)
            ctx.handshake.pq_shared_secret = pq_secret

    verify = _finalise_session(ctx, pq_secret)
    return {"type": "client-finish", "verify": _b64e(verify)}


def server_finish(ctx: TriCrownContext, message: Dict[str, str]) -> None:
    if message.get("type") != "client-finish":
        raise ValueError("unexpected message type")

    pq_secret = ctx.handshake.pq_shared_secret or b""
    expected = _finalise_session(ctx, pq_secret)
    provided = _b64d(message["verify"])
    if not secrets.compare_digest(expected, provided):
        raise ValueError("handshake verification failed")


def _finalise_session(ctx: TriCrownContext, pq_secret: bytes) -> bytes:
    handshake = ctx.handshake
    if handshake.dh_shared_secret is None:
        raise RuntimeError("handshake missing DH shared secret")

    secret_material = handshake.dh_shared_secret + pq_secret
    okm = _hkdf(secret_material, length=96, info=b"tricrown-hybrid-session")
    client_send, server_send, root_key = okm[:32], okm[32:64], okm[64:]

    transcript = handshake.transcript()
    verifier = _hmac(root_key, transcript)

    if ctx.role == "client":
        send_key, recv_key = client_send, server_send
    else:
        send_key, recv_key = server_send, client_send

    ctx.chains = _SessionState(
        rk=root_key,
        send=_CipherState(key=send_key),
        recv=_CipherState(key=recv_key),
    )
    with suppress(AttributeError):
        if handshake.pq_client is not None:
            handshake.pq_client.free()  # type: ignore[attr-defined]
            handshake.pq_client = None
    return verifier


def _hmac(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()


def seal(ctx: TriCrownContext, aad: bytes, plaintext: bytes) -> Dict[str, bytes]:
    session = ctx.require_session()
    cipher = _ChaCha20Poly1305(session.send.key)
    nonce = session.send.next_nonce()
    ciphertext = cipher.encrypt(nonce, plaintext, aad)
    return {"aad": aad, "nonce": nonce, "ct": ciphertext}


def open_(ctx: TriCrownContext, record: Dict[str, bytes]) -> bytes:
    session = ctx.require_session()
    cipher = _ChaCha20Poly1305(session.recv.key)
    nonce = record["nonce"]
    aad = record.get("aad", b"")
    ciphertext = record["ct"]
    return cipher.decrypt(nonce, ciphertext, aad)


def rekey(ctx: TriCrownContext) -> None:
    session = ctx.require_session()
    material = _hkdf(session.rk, length=96, info=b"tricrown-rekey")
    client_send, server_send, new_root = material[:32], material[32:64], material[64:]

    if ctx.role == "client":
        send = client_send
        recv = server_send
    else:
        send = server_send
        recv = client_send

    ctx.chains = _SessionState(
        rk=new_root,
        send=_CipherState(key=send),
        recv=_CipherState(key=recv),
    )


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
