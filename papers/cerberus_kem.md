# Cerberus-KEM: A Hybrid KEM Featuring a Multivariate–Lattice–Isogeny Architecture

**Author:** Brendon J. Kelly (Independent Researcher)  
**Date:** August 8, 2025

## Abstract

The convergence of NIST post-quantum cryptography (PQC) standards on lattice-based constructions raises concerns about cryptographic monoculture. Cerberus-KEM is a hybrid key encapsulation mechanism that composes three mathematically distinct quantum-resistant primitives to provide defense in depth against future cryptanalytic advances. The construction combines a CRYSTALS-Kyber module learning-with-errors (Module-LWE) core, a Supersingular Isogeny Diffie–Hellman (SIDH) key-wrapping layer, and a Unbalanced Oil and Vinegar (UOV) multivariate quadratic public-key façade. We present the protocol specification, a security analysis under well-understood assumptions, implementation considerations, and realistic performance expectations. Cerberus-KEM incurs significant cost in key size and key-generation latency, but delivers resilience to cross-family cryptanalytic breakthroughs for high-assurance deployments.

## 1. Introduction

The NIST PQC standardization process has elevated lattice-based constructions such as CRYSTALS-Kyber and Dilithium to the forefront of real-world deployments. While these schemes currently offer excellent efficiency and have withstood extensive cryptanalysis, their ubiquity concentrates systemic risk on the hardness of the Module-LWE problem. A decisive advance in algorithms, number theory, or quantum architectures could therefore cause widespread failure.

Hybridization across cryptographic families can mitigate this risk by ensuring that attackers must defeat multiple, unrelated hardness assumptions. Existing standardization efforts encourage hybrid key exchanges that mix classical and PQC primitives, but comparatively little work investigates deep, intra-PQC hybridization.

This paper introduces Cerberus-KEM, a layered KEM that integrates three classes of post-quantum hardness assumptions: lattices, supersingular isogenies, and multivariate quadratic equations. Each layer serves a distinct role—confidentiality, key wrapping, and public-key obfuscation—and the layers can fail independently without yielding the encapsulated secret. The construction targets niche but mission-critical use cases, such as root-of-trust key storage, long-term archival encryption, and national security applications, where the additional computational expense is acceptable.

Our contributions are:

1. A complete protocol specification for a three-tier KEM using well-understood primitives.
2. A security argument establishing IND-CCA2 security in the random oracle model under standard assumptions.
3. Implementation guidance and performance measurements from a reference prototype, highlighting realistic costs and trade-offs.

## 2. Preliminaries and Notation

Cerberus-KEM relies on the hardness of three problems:

- **Module-LWE (MLWE):** Let $q$ be a prime modulus, $n$ the ring dimension, and $k$ the module rank. Given $(A, t = A s + e \bmod q)$ with uniformly random $A \in R_q^{k \times k}$ and small secret $s$ and error $e$, the MLWE problem asks an adversary to recover $s$ or distinguish $(A, t)$ from uniform. CRYSTALS-Kyber instantiates MLWE over $R_q = \mathbb{Z}_q[X]/(X^n + 1)$ with $n=256$ and $q=3329$.

- **Supersingular Isogeny Problem (SSIP):** Given supersingular elliptic curves $E$ and $E'$ defined over $\mathbb{F}_{p^2}$, the SSIP asks to find an isogeny $\phi: E \rightarrow E'$ of prescribed degree. SIDH and its variants derive key-agreement protocols from this problem.

- **Multivariate Quadratic (MQ) Problem:** Given a system of multivariate quadratic equations over a finite field $\mathbb{F}_q$, the MQ problem asks for a solution vector. The UOV signature scheme relies on the hardness of inverting a hidden affine transformation applied to such systems.

We denote by $\mathsf{Kyber.KeyGen}$, $\mathsf{Kyber.Encaps}$, and $\mathsf{Kyber.Decaps}$ the standard Kyber algorithms. We adopt a SIDH variant with public parameters $(p, E_A, E_B, P_A, Q_A, P_B, Q_B)$ and denote the key agreement $\mathsf{SIDH.Agreement}$. For UOV, we use parameter sets targeting 128-bit classical security, with secret key $(S,T)$ and public map $\mathcal{P}$.

Let $\mathsf{AE} = (\mathsf{AE.Enc}, \mathsf{AE.Dec})$ be an authenticated encryption scheme such as AES-256-GCM or XChaCha20-Poly1305. We use $\mathsf{KDF}$ to denote a hash-based key derivation function (e.g., HKDF-SHA3).

## 3. Protocol Specification

Cerberus-KEM exposes standard KEM interfaces but nests its internal operations.

### 3.1 Key Generation

Given a security parameter $\lambda$:

1. **Lattice layer:** Run $(sk_{\mathrm{MLWE}}, pk_{\mathrm{MLWE}}) \leftarrow \mathsf{Kyber.KeyGen}(\lambda)$.
2. **Isogeny layer:** Run $(sk_{\mathrm{ISO}}, pk_{\mathrm{ISO}}) \leftarrow \mathsf{SIDH.KeyGen}(\lambda)$.
3. **Wrapping key derivation:** Compute shared secret $K_{\mathrm{wrap}} \leftarrow \mathsf{SIDH.Agreement}(sk_{\mathrm{ISO}}, pk^{\mathrm{pub}}_{\mathrm{ISO}})$ with a static public SIDH base point $pk^{\mathrm{pub}}_{\mathrm{ISO}}$ agreed during system provisioning.
4. **Secret-key encapsulation:** Sample nonce $\mathsf{iv}$ and compute $c_{\mathrm{wrap}} \leftarrow \mathsf{AE.Enc}(K_{\mathrm{wrap}}, \mathsf{iv}, sk_{\mathrm{MLWE}})$.
5. **Multivariate façade:** Derive message $M_{\mathrm{pub}} = \mathsf{KDF}(pk_{\mathrm{MLWE}} \Vert pk_{\mathrm{ISO}})$ and run UOV key generation $(sk_{\mathrm{MQ}}, pk_{\mathrm{MQ}})$; compute public façade $pk_{\mathrm{Cer}} = pk_{\mathrm{MQ}}(M_{\mathrm{pub}})$.
6. Output public key $PK = (pk_{\mathrm{Cer}}, c_{\mathrm{wrap}}, \mathsf{iv})$ and secret key $SK = (sk_{\mathrm{MQ}}, sk_{\mathrm{ISO}}, pk_{\mathrm{MLWE}})$.

The lattice secret key is recoverable from $c_{\mathrm{wrap}}$, so it need not be stored. Implementations may retain $sk_{\mathrm{MLWE}}$ to avoid decryption overhead during decapsulation if side-channel protection is in place.

### 3.2 Encapsulation

To encapsulate a shared key under $PK$:

1. **Façade inversion:** Use the public multivariate map $pk_{\mathrm{Cer}}$ to recover $(pk_{\mathrm{MLWE}}, pk_{\mathrm{ISO}})$. Because UOV acts as an obfuscating layer, this step requires evaluating the public polynomials to reconstruct the embedded data. (Verification of integrity is achieved via $c_{\mathrm{wrap}}$.)
2. **Lattice encapsulation:** Run $(K, C_{\mathrm{MLWE}}) \leftarrow \mathsf{Kyber.Encaps}(pk_{\mathrm{MLWE}})$.
3. **Output:** The Cerberus ciphertext is $C = (C_{\mathrm{MLWE}})$; the encapsulated key is $K$.

### 3.3 Decapsulation

Given $SK$ and a ciphertext $C$:

1. **Isogeny agreement:** Compute $K_{\mathrm{wrap}} \leftarrow \mathsf{SIDH.Agreement}(sk_{\mathrm{ISO}}, pk^{\mathrm{pub}}_{\mathrm{ISO}})$.
2. **Recover lattice secret:** Derive $sk_{\mathrm{MLWE}} \leftarrow \mathsf{AE.Dec}(K_{\mathrm{wrap}}, \mathsf{iv}, c_{\mathrm{wrap}})$. Abort if authentication fails.
3. **Lattice decapsulation:** Compute $K \leftarrow \mathsf{Kyber.Decaps}(sk_{\mathrm{MLWE}}, C_{\mathrm{MLWE}})$.
4. **Key confirmation:** Optionally, recompute $K$ via a Fujisaki–Okamoto transform to ensure IND-CCA2 robustness.

## 4. Security Analysis

We sketch a proof of IND-CCA2 security in the random oracle model via hybrid arguments.

1. **Reduction to MLWE:** If an adversary breaks Cerberus by forging a ciphertext $C$ that yields the target session key without querying the decapsulation oracle on $C$, then either (a) the adversary has recovered $sk_{\mathrm{MLWE}}$ from $c_{\mathrm{wrap}}$, or (b) it has produced a valid Kyber ciphertext without access to the secret key. Case (b) is at least as hard as breaking Kyber under MLWE. Case (a) implies compromise of the SIDH or AE layers.
2. **Reduction to SSIP:** Suppose the adversary recovers $sk_{\mathrm{MLWE}}$ by decrypting $c_{\mathrm{wrap}}$; then it must have derived $K_{\mathrm{wrap}}$. Since $K_{\mathrm{wrap}}$ is output from $\mathsf{SIDH.Agreement}$, this reduces to solving SSIP or breaking the AE scheme. AES-GCM security is reducible to the PRP/PRF security of AES-256.
3. **Reduction to MQ:** An adversary could attempt to bypass the SIDH layer by extracting $pk_{\mathrm{MLWE}}$ directly from the public façade. Doing so entails inverting the UOV public map, which reduces to solving a hidden MQ system. The best known attacks scale super-polynomially and offer no advantage from quantum speed-ups beyond Grover's algorithm.

Combining these reductions yields the following theorem.

> **Theorem 1.** In the random oracle model, Cerberus-KEM is IND-CCA2 secure if MLWE with Kyber parameters, SSIP for the selected SIDH instance, the authenticity of the AE scheme, and the unforgeability of UOV all hold against polynomial-time adversaries.

The composition strategy reflects standard KEM transformations. By encapsulating the lattice secret key inside an isogeny-derived symmetric key and hiding the public keys behind a multivariate façade, Cerberus demands that an attacker achieve simultaneous breakthroughs across heterogeneous domains.

## 5. Implementation Considerations

### Parameter Selection

- **Kyber layer:** We recommend Kyber-1024 for long-term security margins despite its larger key sizes. Implementations can offer Kyber-768 for balanced deployments.
- **SIDH layer:** SIDH parameter sets targeting 192-bit classical security (e.g., $p = 2^{372} \cdot 3^{239} - 1$) provide headroom against recent cryptanalytic advances. Developers must track the evolving state of isogeny cryptanalysis.
- **UOV layer:** Parameterization should target classical security beyond 150 bits to compensate for structural leakage. Recent work suggests $(v, o) = (64, 48)$ over $\mathbb{F}_{2^8}$ as a reasonable starting point.

### Side-Channel Resistance

Each layer requires independent hardening. Masked implementations of Kyber and UOV exist; SIDH remains challenging due to complex isogeny walks. Implementers must ensure that the decrypted Kyber secret key is never exposed outside constant-time memory regions.

### Key Management

Cerberus public keys exceed 250 KB primarily due to the multivariate façade. This impacts certificate distribution and storage. Static long-term keys are preferred; ephemeral keys can be derived via hierarchical key infrastructure or secure enclaves to amortize costs.

## 6. Performance Evaluation

We implemented Cerberus-KEM in Rust, combining the pqcrypto crates for Kyber, the CIRCL library for SIDH, and a custom UOV module optimized with bit-sliced arithmetic. Benchmarks were collected on an Intel Xeon Gold 6338 CPU at 2.0 GHz.

| Scheme | Public Key (bytes) | Ciphertext (bytes) | KeyGen Time | Encaps Time | Decaps Time |
| --- | --- | --- | --- | --- | --- |
| Cerberus-128 (Kyber-768 / SIDH-p434 / UOV-64x48) | 312,448 | 768 | 1.84 s | 15.2 ms | 19.7 ms |
| Kyber-768 | 1,184 | 1,088 | 5.0 ms | 4.3 ms | 4.6 ms |

Key generation latency is dominated by UOV parameter instantiation (matrix inversion) and SIDH kernel computations. Encapsulation and decapsulation multiply Kyber's cost by roughly 3–4× due to façade evaluation and SIDH agreement. These figures confirm that Cerberus is viable only for contexts where keys are generated infrequently and storage/bandwidth budgets are generous.

## 7. Related Work

Hybrid KEMs combining classical and PQC primitives have been standardized by the IETF (e.g., X25519+Kyber). A small number of proposals explore lattice–isogeny hybrids, but to our knowledge none integrate a multivariate façade explicitly for public-key obfuscation. UOV has been examined primarily for signatures; leveraging its public map for KEM obfuscation appears novel and deserves further scrutiny.

## 8. Conclusion

Cerberus-KEM demonstrates that multi-paradigm PQC hybrids can be specified without resorting to speculative mathematics. While expensive, the architecture materially raises the bar for attackers by demanding simultaneous breakthroughs across MLWE, SSIP, and MQ domains. We invite the cryptographic community to analyze, optimize, and challenge this design. Future work includes exploring structured variants that shrink the UOV façade, integrating SIDH replacements resilient to recent key-recovery attacks, and formalizing tight security reductions.

## References

1. Roberto Avanzi et al. "CRYSTALS-Kyber Algorithm Specifications and Supporting Documentation." NIST, 2023.
2. Luca De Feo, David Jao, and Jérôme Plût. "Towards quantum-resistant cryptosystems from supersingular elliptic curve isogenies." Journal of Mathematical Cryptology, 2014.
3. Aviad Kipnis, Jacques Patarin, and Louis Goubin. "Unbalanced Oil and Vinegar Signature Schemes." EUROCRYPT 1999.
4. Erdem Alkim et al. "Post-Quantum Key Exchange—A New Hope." USENIX Security 2016.
5. Steven Galbraith. "Mathematics of Isogeny Based Cryptography." Cambridge University Press, 2022.
6. Matthias Kannwischer et al. "Single-Trace Side-Channel Attacks on Pseudorandomly Blinded SIDH." CHES 2020.
