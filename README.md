# TRI-CROWN 2.0 reference helpers

This repository contains a compact Python reference implementation of the
**TRI-CROWN 2.0** post-quantum hybrid encryption suite.  The code focuses on
the glue logic required to orchestrate the triple-hybrid KEM handshake,
authenticated transcript commitments, deterministic nonces, and record-layer
ratchets described in the specification.

## Layout

- `tricrown/crypto.py` – HKDF helpers, transcript hashing, deterministic
  commitments, and nonce/key derivation.
- `tricrown/pq.py` – lightweight interfaces and deterministic stubs for
  ML-KEM, Classic McEliece, and ML-DSA style primitives.  Replace these stubs
  with bindings to `liboqs` or another PQ provider in production.
- `tricrown/session.py` – high level handshake orchestration, record-layer
  helpers, AEAD backend abstraction, and PQ rekey support.
- `examples/handshake_demo.py` – a minimal script that runs the handshake and
  seals a single record end-to-end using the reference helpers.

## Usage

Create a virtual environment with `cryptography` (and optionally `PyNaCl` for
XChaCha20-Poly1305 support).  Then run:

```bash
python examples/handshake_demo.py
```

The example uses deterministic stubs for the PQ algorithms so that it can be
executed without heavyweight dependencies.  Integrators should replace
`tricrown.pq` with bindings to real ML-KEM, Classic-McEliece, ML-DSA, and
SPHINCS+ implementations before deploying the suite.

## Status

This code is intentionally conservative and aims to be easy to audit.  It is
not a drop-in replacement for a full-featured secure channel protocol.  The
reference is best used as a pedagogical guide or as scaffolding for prototype
implementations that will later integrate hardened, side-channel-resistant
libraries.
