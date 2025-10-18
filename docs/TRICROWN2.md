# TRI-CROWN 2.0 — Max PQ-Hybrid Encryption Suite

The TRI-CROWN 2.0 suite defines a crypto-agile, post-quantum-first secure channel design that composes multiple public, widely-reviewed primitives for maximal robustness. This document captures the baseline profile alongside optional interoperability configurations.

## 0. Suite Identifiers

| Profile | Identifier | Notes |
| --- | --- | --- |
| Default post-quantum | `TRICROWN2-PQ` | Preferred configuration |
| PQ + China compatibility | `TRICROWN2-PQ-SM` | Enables RFC 8998 algorithms when mandated |
| PQ + Russia compatibility | `TRICROWN2-PQ-GOST` | Enables RFC 9227 and IETF GOST algorithms under explicit policy |

## 1. Cryptographic Algorithms

All primitives are standardized with public specifications. The suite is designed for crypto agility and layered assurance.

### Key Encapsulation (Hybrid)

* **ML-KEM-1024** (Kyber-1024)
* **Classic McEliece 6960119** (use 6688128 when bandwidth constrained)
* **X25519** ECDH (ephemeral-ephemeral) as a classical hedge
* Optional: **HQC-256** as an additional PQ KEM when both peers negotiate it

### Signatures (Authentication)

* Default: **ML-DSA** (Dilithium-3)
* Fallback: **SLH-DSA** (SPHINCS+ SHAKE-128s)
* Legacy interop: classical ECDSA only when unavoidable

### KDF and Hashing

* **HKDF-SHA3-512** for extract/expand
* Transcript and commitments use **SHA3-512** and **SHA3-256** respectively

### Authenticated Encryption (Key-Committing)

* Preferred: **AES-256-GCM-SIV**
* Alternative: **XChaCha20-Poly1305**

### Deterministic Nonces

Nonces derive from the chain key and sequence number; random nonces are never used, preventing reuse by construction.

### Ratchets and PQ Re-encapsulation

* Symmetric send/receive chain-key ratchets
* In-band PQ re-encapsulation every **N = 64 messages** or **Δt = 5 minutes**, whichever occurs first

### Compatibility Profiles (off by default)

* **SM profile:** SM2 signatures, SM3 hash, SM4-GCM/CCM per RFC 8998 when policy and peer requirements permit
* **GOST profile:** Kuznyechik/Magma with MGM AEAD, Streebog hash, and GOST EC signatures per relevant IETF RFCs; legal clearance required

## 2. Handshake Protocol

The reference flow below assumes mutual authentication. Server-authenticated-only flows are subsets.

### Long-Term and Ephemeral Keys

* Client holds `(pk_ML, sk_ML)`, `(pk_McE, sk_McE)`, and an ephemeral X25519 key pair
* Server holds `(PK_ML, SK_ML)`, `(PK_McE, SK_McE)`, and an ephemeral X25519 key pair

### Message Flow

1. **ClientHello:** advertises suite list, includes X25519 ephemeral `Xe_c`, optional client PQ public keys, and random session identifier `sid`. Transcript hash `th0` starts here.
2. **ServerHello:** selects suite, provides `Xe_s`, and server PQ public keys. Transcript updates to `th1`.
3. **Encapsulations:** Client produces `(ct_ML_c, ss_ML_c)` and `(ct_McE_c, ss_McE_c)`; computes `ss_X = x25519(Xe_c, Xe_s)`; sends all ciphertexts.
4. **Decapsulation:** Server decapsulates and may optionally send server-to-client PQ encapsulations for reciprocity.
5. **Key Schedule:**
   * `mix = HKDF-Extract(salt = th1, IKM = concat(ss_ML_c, ss_McE_c, ss_X [, ss_ML_s, ss_McE_s]))`
   * `hs = HKDF-Expand(mix, info = "TRICROWN2 hs" || suite || context, L = 128)`
   * Split `hs` into `{rk0, ck_s0, ck_r0, k_commit, k_nonce}`
6. **Authentication:** Both parties sign `th1 || all_cts` with ML-DSA (or SLH-DSA fallback) and verify signatures.

Suite negotiation values appear in the transcript and associated data to enforce downgrade resistance.

## 3. Record Layer

* **Header:** `{suite_id, sid, seq, aad_len, ct_len}`
* **Nonce:** `nonce = HKDF-Expand(k_nonce, info = "nonce" || seq, L = 12 or 24)`

### Sending (`seal`)

1. Derive message key `mk = HKDF-Expand(ck_s, info = "mk" || seq, L = 32)`
2. Advance the send chain key: `ck_s = HKDF-Extract("step", ck_s)`
3. Encrypt with AEAD `(mk, nonce, aad)` to produce `(ct, tag)`
4. Compute key-commitment `commit = SHA3-256(k_commit || suite_id || sid || seq || nonce || aad || ct)`
5. Transmit header, ciphertext, and commitment (verify-before-decrypt discipline)

### Receiving (`open`)

1. Verify `commit` prior to AEAD processing
2. Derive message key and advance receive chain key in lock-step
3. Decrypt with matching AEAD configuration

## 4. PQ Refresh

Trigger new PQ encapsulations every 64 messages or 5 minutes, whichever occurs first. Mix fresh shared secrets with the current transcript via HKDF to renew `{rk, ck_s, ck_r, k_commit, k_nonce}`.

## 5. Security Properties

* Confidentiality and authenticity survive if any of `{ML-KEM, Classic McEliece, X25519}` remains unbroken and the AEAD is sound
* Deterministic nonces eliminate reuse risk
* Key commitments prevent key swapping and bind metadata
* Ratchets plus periodic PQ refresh provide forward secrecy with bounded exposure
* Transcript binding thwarts downgrades and parameter confusion

## 6. Engineering Considerations

* Classic McEliece public keys can be several megabytes; pin and pre-distribute long-term server PQ keys
* Enforce constant-time decapsulation; prefer masked ML-KEM implementations when available
* Zeroize ephemeral secrets promptly
* Limit logging to metadata digests—never persist key material

## 7. API Skeleton

```
init(role, suite_id, my_auth_keys, peer_auth_pub, policy) -> ctx
handshake_send(ctx) -> flight_bytes
handshake_recv(ctx, flight_bytes) -> status/next
seal(ctx, aad, plaintext) -> record
open(ctx, record) -> plaintext
rekey(ctx)  # triggers PQ refresh
close(ctx)
```

## 8. Python Reference Skeleton

The following illustrative code shows how the suite components can be wired together using Python. Replace the placeholder PQ primitives with audited bindings such as liboqs.

```python
from dataclasses import dataclass
from hashlib import sha3_256, sha3_512
from hmac import compare_digest
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
import os

# === PQ stubs (replace with liboqs bindings) ===
class MLKEM:
    @staticmethod
    def keygen(): return b"mlkem_pk", b"mlkem_sk"
    @staticmethod
    def encap(pk): return b"mlkem_ct", os.urandom(32)
    @staticmethod
    def decap(ct, sk): return os.urandom(32)

class McEliece:
    @staticmethod
    def keygen(): return b"mce_pk", b"mce_sk"
    @staticmethod
    def encap(pk): return b"mce_ct", os.urandom(32)
    @staticmethod
    def decap(ct, sk): return os.urandom(32)

# === HKDF helpers ===
def hkdf_extract(salt:bytes, ikm:bytes)->bytes:
    return HKDF(algorithm=hashes.SHA3_512(), length=64, salt=salt, info=b"TRICROWN2 extract").derive(ikm)

def hkdf_expand(prk:bytes, info:bytes, L:int)->bytes:
    return HKDF(algorithm=hashes.SHA3_512(), length=L, salt=None, info=info).derive(prk)

@dataclass
class Chains:
    rk: bytes
    ck_s: bytes
    ck_r: bytes
    k_commit: bytes
    k_nonce: bytes

@dataclass
class Ctx:
    role: str
    suite: str
    sid: bytes
    th: bytes
    chains: Chains
    x_sk: x25519.X25519PrivateKey
    x_pk: x25519.X25519PublicKey
    peer_x_pk: x25519.X25519PublicKey|None
    ml_sk: bytes|None
    ml_pk: bytes|None
    mce_sk: bytes|None
    mce_pk: bytes|None
    seq_s: int = 0
    seq_r: int = 0
    aead: str = "AES-GCM-SIV"  # or "XChaCha20"

SUITE_ID = b"TRICROWN2-PQ"

# === Transcript & commitment ===

def transcript_hash(parts:list[bytes])->bytes:
    h=sha3_512(); [h.update(p) for p in parts]; return h.digest()

def commit_tag(kc:bytes, sid:bytes, seq:int, nonce:bytes, aad:bytes, ct:bytes)->bytes:
    h=sha3_256();
    for b in (kc, SUITE_ID, sid, seq.to_bytes(8,'big'), nonce, aad, ct): h.update(b)
    return h.digest()

# === Nonce & key schedule ===

def derive_nonce(k_nonce:bytes, seq:int, nlen:int)->bytes:
    return hkdf_expand(k_nonce, b"nonce"+seq.to_bytes(8,'big'), nlen)

def next_mk(ck:bytes, seq:int)->tuple[bytes,bytes]:
    mk = hkdf_expand(ck, b"mk"+seq.to_bytes(8,'big'), 32)
    ck2 = hkdf_extract(b"step", ck)
    return mk, ck2

# === Client handshake (server-auth for brevity) ===

def client_init()->Ctx:
    x_sk=x25519.X25519PrivateKey.generate(); x_pk=x_sk.public_key()
    ml_pk, ml_sk = MLKEM.keygen(); mce_pk, mce_sk = McEliece.keygen()
    sid=os.urandom(16)
    chains=Chains(b"",b"",b"",b"",b"")
    return Ctx("client", SUITE_ID.decode(), sid, b"", chains, x_sk, x_pk, None, ml_sk, ml_pk, mce_sk, mce_pk)

def client_hello(ctx:Ctx)->bytes:
    msg=b"CHLO|"+SUITE_ID+b"|"+ctx.x_pk.public_bytes_raw()+b"|"+ctx.ml_pk+b"|"+ctx.mce_pk
    ctx.th=transcript_hash([msg]); return msg

def server_hello(ctx_srv:Ctx, chlo:bytes)->bytes:
    Xe_c=x25519.X25519PublicKey.from_public_bytes(chlo.split(b"|")[2])
    ctx_srv.peer_x_pk=Xe_c
    msg=b"SHLO|"+SUITE_ID+b"|"+ctx_srv.x_pk.public_bytes_raw()+b"|"+ctx_srv.ml_pk+b"|"+ctx_srv.mce_pk
    ctx_srv.th=transcript_hash([chlo,msg]); return msg

def client_send_kems(ctx:Ctx, shlo:bytes, PK_ML:bytes, PK_McE:bytes, Xe_s_bytes:bytes)->bytes:
    Xe_s=x25519.X25519PublicKey.from_public_bytes(Xe_s_bytes)
    ss_X=ctx.x_sk.exchange(Xe_s)
    ct_ml, ss_ml = MLKEM.encap(PK_ML)
    ct_mce, ss_mce = McEliece.encap(PK_McE)
    mix=hkdf_extract(ctx.th, ss_ml+ss_mce+ss_X)
    hs=hkdf_expand(mix, b"TRICROWN2 hs"+SUITE_ID, 128)
    ctx.chains=Chains(hs[0:32], hs[32:64], hs[64:96], hs[96:128-32], hs[128-32:128])
    msg=b"CTs|"+ct_ml+b"|"+ct_mce
    ctx.th=transcript_hash([ctx.th,msg]); return msg

# === Record layer ===

def seal(ctx:Ctx, aad:bytes, pt:bytes)->dict:
    seq=ctx.seq_s; ctx.seq_s+=1
    mk, ctx.chains.ck_s = next_mk(ctx.chains.ck_s, seq)
    if ctx.aead=="AES-GCM-SIV":
        aead=AESGCM(mk); nonce=derive_nonce(ctx.chains.k_nonce, seq, 12)
    else:
        aead=ChaCha20Poly1305(mk); nonce=derive_nonce(ctx.chains.k_nonce, seq, 24)
    ct=aead.encrypt(nonce, pt, aad)
    commit=commit_tag(ctx.chains.k_commit, ctx.sid, seq, nonce, aad, ct)
    return {"seq":seq, "nonce":nonce, "aad":aad, "ct":ct, "commit":commit}

def open_(ctx:Ctx, rec:dict)->bytes:
    seq=rec["seq"]
    exp=commit_tag(ctx.chains.k_commit, ctx.sid, seq, rec["nonce"], rec["aad"], rec["ct"])
    if not compare_digest(exp, rec["commit"]):
        raise ValueError("commitment mismatch")
    mk, ctx.chains.ck_r = next_mk(ctx.chains.ck_r, seq)
    if ctx.aead=="AES-GCM-SIV": aead=AESGCM(mk)
    else: aead=ChaCha20Poly1305(mk)
    return aead.decrypt(rec["nonce"], rec["ct"], rec["aad"])
```

## 9. Policy and Compliance Gates

* Default to `TRICROWN2-PQ`; enable `-SM` or `-GOST` only under explicit legal and policy requirements
* Review export controls for GOST profiles before involving U.S. persons
* Maintain continuous KATs and interoperability testing across liboqs releases

## 10. Practical Strengths

* Parallel PQ assumptions (ML-KEM, Classic McEliece) plus a classical hedge
* Key-commitments verified prior to decryption
* Deterministic nonces and per-message ratchets
* Scheduled PQ refresh for ongoing forward secrecy
* Strict transcript and AAD binding to defeat downgrades
* Standards-only primitives with explicit crypto agility
