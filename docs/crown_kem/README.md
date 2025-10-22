# Crown-KEM Reference Package

This folder captures the documentation artifacts for the HYBRID-KEM v1 reference stack that pairs the Crown-KEM hybrid primitive suite with the K-Math provenance layer.

## Contents

- `crown_kem_technical_memo.tex` – full technical memo that summarises priority primitives, engineering tasks, and the HYBRID-KEM v1 specification.
- `integration_matrix.csv` – triage table of the most relevant research items that influence the hardening roadmap.
- `provenance_checklist.md` – operational checklist for establishing an auditable Git/GPG provenance chain.
- `sol_v1_license_form.tex` – Sovereign Attribution & License (SOL v1.0) fillable form to accompany releases.

## Implementation outline

Reference code should follow the proposed module layout:

```
/primitives
  ml_kem.rs       # shim to pqclean/liboqs
  mc_eliece.rs
  fhe_kernel.rs   # optional BFV/CKKS kernel

/hybrid
  hybrid_transform.rs
  ktoken.rs

/protocols
  dkg.rs
  pake.rs
  zk_wrappers.rs

/hardening
  masking.rs
  sidechannel_tests.rs
  emfi_detector.rs

/tests
  test_vectors/
  leakage_tests/
```

The package is specification-first. Implementations must integrate hardened, constant-time primitives from vetted libraries such as [`liboqs`](https://github.com/open-quantum-safe/liboqs) or [`pqclean`](https://github.com/pqclean/pqclean) and wrap them with the deterministic hybrid transform defined in the memo. All artifacts in this folder are audit-friendly and exclude exploit material.
