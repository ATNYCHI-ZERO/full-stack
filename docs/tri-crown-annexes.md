# TRI-CROWN Annexes — Process Matrix, Kalman Falling Body, and Robust Text/Cipher Tools

This document extends the base TRI-CROWN suite with linear-systems mathematics, dynamic programming, text and cipher analytics, and a Kalman model for the falling-body problem.

---

## A. Process Matrix, DP Diagonalization, and Text-Cipher Harmonics

### A1. Process Matrix with Mean-Squared Deviation and Inhomogeneous Term

Consider the continuous linear stochastic differential equation (SDE):

\[
\dot x(t) = A x(t) + B u(t) + G w(t),
\]

where \(w\) is white noise with \(\mathbb{E}[w w^T] = Q_c \delta\). The process matrix is

\[
\Phi(\Delta t) = e^{A \Delta t}.
\]

The inhomogeneous solution is

\[
 x_{k+1} = \Phi x_k + \int_0^{\Delta t} \Phi(\Delta t - \tau) B u(t_k + \tau) \, d\tau + w_d.
\]

The discrete process noise is computed as

\[
 Q_d = \int_0^{\Delta t} \Phi(\tau) G Q_c G^T \Phi(\tau)^T \, d\tau.
\]

The mean-squared deviation (MSD) is

\[
 \mathrm{MSD} = \mathbb{E}\|x - \mu\|^2 = \operatorname{tr}(P) + (\mu - \bar x)^T(\mu - \bar x),
\]

where \(P\) is the covariance matrix. The Van Loan block exponential provides a convenient way to compute \(\Phi\) and \(Q_d\):

\[
\exp\left(
\begin{bmatrix}
 -A & G Q_c G^T \\
 0 & A^T
\end{bmatrix}
\Delta t\right) =
\begin{bmatrix}
 \Phi & Q_d \\
 0 & \Phi^{-T}
\end{bmatrix}.
\]

### A2. Diagonal Form and Dynamic Programming

If \(A = V \Lambda V^{-1}\) then \(\Phi = V e^{\Lambda \Delta t} V^{-1}\). For a finite-horizon Linear Quadratic Regulator (LQR), dynamic programming yields the recursion

\[
 J_k(x) = \min_u \left\{ x^T Q x + u^T R u + J_{k+1}(F x + B u) \right\}.
\]

The discrete Riccati equation is

\[
 P_k = Q + F^T \left(P_{k+1} - P_{k+1} B (R + B^T P_{k+1} B)^{-1} B^T P_{k+1}\right) F.
\]

### A3. Convolution via Runge–Kutta

Approximate the integral

\[
 \int_0^{\Delta t} \Phi(\Delta t - \tau) B u(t_k + \tau) \, d\tau
\]

using Runge–Kutta 4 (RK4) nodes or Simpson's rule. These methods are stable for piecewise-smooth control inputs \(u\).

### A4. Caesar/Digram Harmonic Conduit

Treat the alphabet as the group \(G = \mathbb{Z}_{26}\). A Caesar shift corresponds to adding \(s \in G\). Reversal is the automorphism \(x \mapsto -x\). Compute digram frequencies by counting letter pairs, optionally filtering using an interrogatives dictionary. Use the subgroup \(\langle 13 \rangle\) for parity checks. Magic-square permutations can serve as S-boxes, and Cantor pairing provides pair encodings.

### A5. Robust Huber IRLS and Fixed-Point Guard

For the Huber loss \(\rho_\delta(r)\), the iteratively reweighted least squares (IRLS) weights are

\[
 w_i = \min(1, \delta / |r_i|).
\]

Detect cryptographic fixed-point cycles by rejecting keys derived from the HKDF update \(K = \mathrm{HKDF}(K, \cdot)\).

### A6. Minimal Python Example (Robust Fit + Caesar Digrams)

```python
import numpy as np

def huber_irls(X, y, delta=1.0, w=None, steps=20):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    n, p = X.shape
    w = np.ones(n) if w is None else np.asarray(w, float)
    beta = np.linalg.lstsq(X * np.sqrt(w[:, None]), y * np.sqrt(w), rcond=None)[0]
    for _ in range(steps):
        r = y - X @ beta
        s = np.maximum(np.abs(r), 1e-12)
        w = np.minimum(1.0, delta / s)
        beta = np.linalg.lstsq(X * np.sqrt(w[:, None]), y * np.sqrt(w), rcond=None)[0]
    return beta

ALPH = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
idx = {c: i for i, c in enumerate(ALPH)}

def caesar(s, shift):
    t = []
    for ch in s.upper():
        if ch in idx:
            t.append(ALPH[(idx[ch] + shift) % 26])
        else:
            t.append(ch)
    return ''.join(t)

def digram_counts(s):
    s = [c for c in s.upper() if c in idx]
    from collections import Counter
    return Counter(''.join(s[i:i+2]) for i in range(len(s) - 1))
```

---

## B. Kalman Filtering: Falling-Body Model (With and Without Drag)

### B1. Models

Let the state be \(x = [h, v]^T\), representing height and velocity, with gravity \(g > 0\) and sampling interval \(\Delta t\).

**No drag:**

\[
F = \begin{bmatrix}1 & \Delta t \\ 0 & 1\end{bmatrix}, \quad
B = \begin{bmatrix}\tfrac{1}{2} \Delta t^2 \\ \Delta t\end{bmatrix}, \quad
u = -g.
\]

Process noise from white acceleration with power spectral density (PSD) \(q\) gives

\[
Q = q \begin{bmatrix} \tfrac{\Delta t^3}{3} & \tfrac{\Delta t^2}{2} \\ \tfrac{\Delta t^2}{2} & \Delta t \end{bmatrix}.
\]

Assuming height measurements, the observation model is \(H = [1 \; 0]\) with measurement noise covariance \(R = \sigma_z^2\).

**Linear drag (\(\dot v = -g - \beta v\)):**

\[
A = \begin{bmatrix}0 & 1 \\ 0 & -\beta\end{bmatrix},
\]

with exact discretization

\[
\Phi = e^{A \Delta t} =
\begin{bmatrix}
1 + \tfrac{1 - e^{-\beta \Delta t}}{\beta} & \tfrac{1 - e^{-\beta \Delta t}}{\beta} \\
0 & e^{-\beta \Delta t}
\end{bmatrix}.
\]

Use the Van Loan method with continuous noise input matrix \(G = [0 \; 1]^T\) and \(Q_c = q\) to compute the discrete \(Q\).

### B2. Filter Recursion

Prediction:

\[
\hat x^- = F \hat x + B u,
\qquad P^- = F P F^T + Q.
\]

Update:

\[
K = P^- H^T (H P^- H^T + R)^{-1},
\qquad \hat x = \hat x^- + K (z - H \hat x^-),
\qquad P = (I - K H) P^-.
\]

### B3. Python Reference Implementation

```python
import numpy as np

def discretize_lin_drag(dt, beta):
    if beta <= 0:  # no drag
        F = np.array([[1.0, dt], [0.0, 1.0]])
        return F
    eb = np.exp(-beta * dt)
    a = (1.0 - eb) / beta
    F = np.array([[1.0 + a, a], [0.0, eb]])
    return F

def Q_acc(dt, q):
    dt2, dt3 = dt * dt, dt * dt * dt
    return q * np.array([[dt3 / 3.0, dt2 / 2.0], [dt2 / 2.0, dt]])

def kf_step(x, P, z, F, B, u, H, Q, R):
    # Predict
    x_ = F @ x + B * u
    P_ = F @ P @ F.T + Q
    # Update
    S = H @ P_ @ H.T + R
    K = P_ @ H.T @ np.linalg.inv(S)
    y = z - H @ x_
    x = x_ + K @ y
    P = (np.eye(len(P)) - K @ H) @ P_
    return x, P, K, S

# Example usage
DT = 0.01
G = 9.80665
q = 1e-2
beta = 0.0
F = discretize_lin_drag(DT, beta)
B = np.array([[0.5 * DT * DT], [DT]])
H = np.array([[1.0, 0.0]])
Q = Q_acc(DT, q)
R = np.array([[0.5 ** 2]])  # 0.5 m standard deviation
x = np.array([[100.0], [0.0]])  # 100 m height, 0 m/s velocity
P = np.diag([10.0, 10.0])
z = np.array([[99.95]])
x, P, K, S = kf_step(x, P, z, F, B, -G, H, Q, R)
```

---

## C. TRI-CROWN 1.0 — Aggressive PQ-Hybrid Encryption Suite

**Goal:** Achieve maximal safety against classical and quantum threats with pragmatic deployability. The suite employs a triple-hybrid KEM, key-committing AEAD, deterministic nonces, transcript binding, ratchets, and periodic post-quantum re-encapsulation.

### C1. Ciphersuite Summary

- **KEM (triple-hybrid):** ML-KEM-1024 ∥ Classic-McEliece-6960119 (or 6688128) ∥ X25519 ECDH (ephemeral-ephemeral).
- **Signature (authentication):** ML-DSA (Dilithium-3) by default; SPHINCS+-SHAKE-128s as fallback.
- **KDF / hash:** HKDF-SHA3-512; transcript hash uses SHA3-512.
- **AEAD:** AES-256-GCM-SIV (preferred) or XChaCha20-Poly1305, both in key-committing mode.
- **Nonce:** Deterministic from ratchet state and counters; no random nonces.
- **Ratchets:** Symmetric per-message ratchet plus PQ re-encapsulation every \(N\) messages or after a time interval \(\Delta t\).
- **Metadata in AAD:** {version, suite_id, session_id, peer_ids, counters, PQ_levels}.
- **Side-channel discipline:** Constant-time operations, masked ML-KEM decapsulation, and secret wiping.

Suite ID: `TRICROWN-1.0`. Security target: at least NIST Category 5 for PQ components and at least 128-bit classical security.

### C2. Threat Model

- Active man-in-the-middle (MITM), chosen-ciphertext, and state compromise adversaries.
- Nonce misuse and post-quantum adversaries.
- Goals include forward secrecy, key-compromise impersonation resistance, downgrade resistance, key and metadata commitment, and resilience if any single KEM fails.

### C3. Handshake Overview (Mutual or Server Authentication)

**Keys:**

- Client: `(pk_ML, sk_ML)`, `(pk_McE, sk_McE)`, `x25519_ephemeral`.
- Server: `(PK_ML, SK_ML)`, `(PK_McE, SK_McE)`, `x25519_ephemeral`.

**Flow (mutual authentication):**

1. **ClientHello:** Ciphersuite list, client PQ public keys (optional), X25519 ephemeral public `Xe_c`, transcript hash `th0`.
2. **ServerHello:** Chosen suite, server PQ public keys, X25519 ephemeral public `Xe_s`, `th1 = H(th0 || ServerHello)`.
3. **Encapsulations:** Client encapsulates to `PK_ML` and `PK_McE` yielding `(ct_ML_c, ss_ML_c)` and `(ct_McE_c, ss_McE_c)`; computes `ss_X = x25519(Xe_c, Xe_s)`; sends ciphertexts.
4. **ServerDecap:** Server derives shared secrets, optionally encapsulates to client PQ keys for reciprocity producing `(ct_ML_s, ss_ML_s)` and `(ct_McE_s, ss_McE_s)`; sends ciphertexts.
5. **Key mixing:**
   \[
   \text{mix} = \mathrm{HKDF\text{-}Extract}(\text{salt} = th1,\; \text{IKM} = ss_{ML_c} || ss_{McE_c} || ss_X [|| ss_{ML_s} || ss_{McE_s}]).
   \]
   Update transcript hash \(th2 = H(th1 || \text{all ciphertexts})\).
6. **Authentication:** Each party signs \(th2\) with ML-DSA (or SPHINCS+). Verify peer signatures.
7. **Handshake secrets:**
   \[
   hs = \mathrm{HKDF\text{-}Expand}(\text{mix}, \text{info} = \text{"TRICROWN hs"} || \text{context}, L = 96)
   \]
   Split into `rk0` (root key), `ck_s0`, `ck_r0`, and `k_commit`.

Server-authentication-only mode omits client signatures and client PQ public keys for the return encapsulation.

### C4. Transcript Binding and Key Commitment

- Maintain transcript hash \(th = \mathrm{SHA3\text{-}512}\) over all handshake messages.
- Include \(th\) in all HKDF info labels.
- Key-commit tag for each record:
  \[
  \text{commit} = \mathrm{SHA3\text{-}256}(k_{\text{commit}} || \text{suite\_id} || \text{session\_id} || \text{seq} || \text{nonce} || \text{aad} || \text{ct}).
  \]
  Verify before attempting AEAD decryption.

### C5. Record Layer

- **Header:** `{type, version, suite_id, session_id, seq, aad_len, ct_len}`.
- **Nonce derivation:** `nonce = HKDF(ratchet_key, "nonce" || seq, 24)[:12 or 24]`.
- **Sealing procedure:**
  1. `mk = HKDF-Expand(ck_s, "mk" || seq, 32)`; advance `ck_s = HKDF(ck_s, "step", 32)`.
  2. AEAD seal using `mk` and `nonce` with provided AAD.
  3. Compute commitment tag and emit `{header, nonce, commit, ct, tag}`.
- **Opening procedure:** Verify commitment, perform AEAD open with derived `mk` and `nonce`, and advance `ck_r` while supporting a small reordering window.

### C6. Periodic PQ Re-Encapsulation (Refresh)

- Trigger every `N = 64` records or `Δt = 5 minutes`, whichever occurs first.
- Re-run KEM encapsulations within the channel and update `rk`, `ck_s`, `ck_r`, and `k_commit` via HKDF with the new shared secrets and current transcript hash.

### C7. Deterministic Nonces

- Derive nonces from the chain key and sequence number to avoid reuse and ensure auditability.

### C8. Parameter Choices

- ML-KEM: 1024.
- Classic-McEliece: 6960119 (preferred) or 6688128.
- ML-DSA: Dilithium-3.
- SPHINCS+ fallback: SHAKE-128s.
- AEAD: Prefer AES-256-GCM-SIV; XChaCha20-Poly1305 as alternative.

### C9. Downgrade and Context Binding

- Include offered and selected suites, PQ levels, and algorithm OIDs in the transcript and AAD. Reject mismatches.

### C10. RNG and Key Erasure

- Employ a system DRBG (e.g., NIST CTR-DRBG or `/dev/urandom`).
- Zeroize secrets promptly: ephemeral X25519 keys, KEM intermediates, chain keys after use.

### C11. Reference API (Language-Agnostic)

```
init(role, suite_id, my_auth_keys, peer_auth_pub) -> ctx
handshake_send(ctx) -> bytes  # next flight
handshake_recv(ctx, bytes) -> maybe more flights
seal(ctx, aad:bytes, plaintext:bytes) -> record
open(ctx, record) -> plaintext
rekey(ctx)  # triggers PQ refresh
close(ctx)
```

### C12. Python Reference Skeleton

```python
from dataclasses import dataclass
from hashlib import sha3_256, sha3_512
from hmac import compare_digest
import os
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

# === Stubs: replace with PQ libraries ===
class MLKEM:
    @staticmethod
    def keygen():
        return b"mlkem_pk", b"mlkem_sk"

    @staticmethod
    def encap(pk):
        return b"mlkem_ct", os.urandom(32)

    @staticmethod
    def decap(ct, sk):
        return os.urandom(32)


class McEliece:
    @staticmethod
    def keygen():
        return b"mce_pk", b"mce_sk"

    @staticmethod
    def encap(pk):
        return b"mce_ct", os.urandom(32)

    @staticmethod
    def decap(ct, sk):
        return os.urandom(32)


def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA3_512(), length=64, salt=salt, info=b"TRICROWN extract").derive(ikm)


def hkdf_expand(prk: bytes, info: bytes, L: int) -> bytes:
    return HKDF(algorithm=hashes.SHA3_512(), length=L, salt=None, info=info).derive(prk)


@dataclass
class Chains:
    rk: bytes
    ck_s: bytes
    ck_r: bytes
    k_commit: bytes


@dataclass
class Ctx:
    role: str
    suite: str
    sid: bytes
    th: bytes
    chains: Chains
    x_sk: x25519.X25519PrivateKey
    x_pk: x25519.X25519PublicKey
    peer_x_pk: x25519.X25519PublicKey | None
    ml_sk: bytes | None
    ml_pk: bytes | None
    mce_sk: bytes | None
    mce_pk: bytes | None
    seq_s: int = 0
    seq_r: int = 0
    aead: str = "AES-GCM-SIV"  # or "XChaCha20"


SUITE_ID = b"TRICROWN-1.0"


def transcript_hash(msgs: list[bytes]) -> bytes:
    h = sha3_512()
    for m in msgs:
        h.update(m)
    return h.digest()


def commit_tag(kc: bytes, suite_id: bytes, sid: bytes, seq: int, nonce: bytes, aad: bytes, ct: bytes) -> bytes:
    h = sha3_256()
    h.update(kc)
    h.update(suite_id)
    h.update(sid)
    h.update(seq.to_bytes(8, "big"))
    h.update(nonce)
    h.update(aad)
    h.update(ct)
    return h.digest()


def derive_nonce(ck: bytes, seq: int, nlen: int) -> bytes:
    return hkdf_expand(ck, b"nonce" + seq.to_bytes(8, "big"), nlen)


def next_mk(ck: bytes, seq: int) -> tuple[bytes, bytes]:
    mk = hkdf_expand(ck, b"mk" + seq.to_bytes(8, "big"), 32)
    ck2 = hkdf_extract(salt=b"step", ikm=ck)
    return mk, ck2


def client_init() -> Ctx:
    x_sk = x25519.X25519PrivateKey.generate()
    x_pk = x_sk.public_key()
    ml_pk, ml_sk = MLKEM.keygen()
    mce_pk, mce_sk = McEliece.keygen()
    sid = os.urandom(16)
    return Ctx("client", "TRICROWN-1.0", sid, b"", Chains(b"", b"", b"", b""), x_sk, x_pk, None, ml_sk, ml_pk, mce_sk, mce_pk)


def client_handshake1(ctx: Ctx) -> bytes:
    msg = b"CHLO|" + SUITE_ID + b"|" + ctx.x_pk.public_bytes_raw() + b"|" + ctx.ml_pk + b"|" + ctx.mce_pk
    ctx.th = transcript_hash([msg])
    return msg


def server_handshake1(ctx_srv: Ctx, msg1: bytes) -> bytes:
    parts = msg1.split(b"|")
    Xe_c = x25519.X25519PublicKey.from_public_bytes(parts[2])
    ctx_srv.peer_x_pk = Xe_c
    msg = b"SHLO|" + SUITE_ID + b"|" + ctx_srv.x_pk.public_bytes_raw() + b"|" + ctx_srv.ml_pk + b"|" + ctx_srv.mce_pk
    ctx_srv.th = transcript_hash([msg1, msg])
    return msg


def client_send_kems(ctx: Ctx, shlo: bytes, PK_ML: bytes, PK_McE: bytes, Xe_s_bytes: bytes) -> bytes:
    Xe_s = x25519.X25519PublicKey.from_public_bytes(Xe_s_bytes)
    ss_X = ctx.x_sk.exchange(Xe_s)
    ct_ml, ss_ml = MLKEM.encap(PK_ML)
    ct_mce, ss_mce = McEliece.encap(PK_McE)
    mix = hkdf_extract(ctx.th, ss_ml + ss_mce + ss_X)
    hs = hkdf_expand(mix, b"TRICROWN hs" + SUITE_ID, 96)
    ctx.chains = Chains(hs[0:32], hs[32:64], hs[64:96-32], hs[96-32:96])
    msg = b"CTs|" + ct_ml + b"|" + ct_mce
    ctx.th = transcript_hash([ctx.th, msg])
    return msg


def seal(ctx: Ctx, aad: bytes, pt: bytes) -> dict:
    seq = ctx.seq_s
    ctx.seq_s += 1
    mk, ctx.chains.ck_s = next_mk(ctx.chains.ck_s, seq)
    if ctx.aead == "AES-GCM-SIV":
        nonce = derive_nonce(ctx.chains.ck_s, seq, 12)
        aead = AESGCM(mk)
    else:
        nonce = derive_nonce(ctx.chains.ck_s, seq, 24)
        aead = ChaCha20Poly1305(mk)
    ct = aead.encrypt(nonce, pt, aad)
    commit = commit_tag(ctx.chains.k_commit, SUITE_ID, ctx.sid, seq, nonce, aad, ct)
    return {"seq": seq, "nonce": nonce, "aad": aad, "ct": ct, "commit": commit}


def open_(ctx: Ctx, rec: dict) -> bytes:
    seq = rec["seq"]
    mk, ctx.chains.ck_r = next_mk(ctx.chains.ck_r, seq)
    if ctx.aead == "AES-GCM-SIV":
        aead = AESGCM(mk)
    else:
        aead = ChaCha20Poly1305(mk)
    expect = commit_tag(ctx.chains.k_commit, SUITE_ID, ctx.sid, seq, rec["nonce"], rec["aad"], rec["ct"])
    if not compare_digest(expect, rec["commit"]):
        raise ValueError("commitment mismatch")
    return aead.decrypt(rec["nonce"], rec["ct"], rec["aad"])
```

### C13. Re-Encapsulation API

```
rekey(ctx):
  # Perform new KEM encapsulations within the channel
  derive new shared secrets → mix' = HKDF-Extract(salt = th, IKM = ss_* || rk)
  hs' = HKDF-Expand(mix', info = "TRICROWN hs'" || th, L = 96)
  chains := (rk', ck_s', ck_r', k_commit')
```

### C14. Audit Checklist

- ML-KEM decapsulation must be masked.
- X25519 ephemeral keys are unique per handshake.
- AEAD keys are distinct for each direction.
- Nonces are deterministic and unique.
- Commitment tags are verified before decryption.
- Transcript includes suite negotiation and keys.
- Operations are constant-time for decapsulation, comparisons, and tag handling.
- Old chain keys and message keys are wiped after use.

### C15. Implementation Notes

- Replace stubs with audited libraries.
- Adjust `N` and `Δt` for re-encapsulation based on latency and throughput requirements.
- Consider SPHINCS+ when side-channel resistance is a priority despite larger signatures.
