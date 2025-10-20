# TRI-CROWN: A Triple-Hybrid Key Encapsulation Mechanism for Algorithmic Diversity and Long-Term Resilience

**Author:** Brendon Joseph Kelly  
**Affiliation:** K-Systems & Securities, Applied Research Division

**Abstract.** The cryptographic community is transitioning to post-quantum cryptography, yet confidence in any single new family of algorithms is still developing. Standard hybrid schemes, which combine a classical primitive with a single post-quantum primitive, provide a crucial safety net but remain vulnerable to a systemic break in the chosen post-quantum family. To address this, we propose TRI-CROWN, a high-assurance, triple-hybrid Key Encapsulation Mechanism (KEM) designed for maximum resilience in high-stakes environments.

TRI-CROWN orchestrates a key exchange using three cryptographically dissimilar primitives: X25519 (elliptic-curve cryptography), ML-KEM (lattice-based cryptography), and Classic McEliece (code-based cryptography). By deriving a shared secret from the outputs of all three, the protocol's security is predicated on the hardness of at least one of the underlying mathematical problems. An adversary must possess the capability to break ECC, lattice-based schemes, *and* code-based schemes to compromise the key exchange. This principle of deep algorithmic diversity provides a robust defense against future cryptanalytic breakthroughs that might neutralize an entire class of algorithms.

The protocol further incorporates a full transcript hash for key commitment and a forward-secure key schedule with ratcheting capabilities. We present the formal construction of the protocol, its key derivation framework, and a security rationale for its conservative design, positioning TRI-CROWN as a blueprint for next-generation secure channels requiring long-term, multi-generational security.

**Keywords:** Post-Quantum Cryptography, Hybrid Encryption, Key Encapsulation Mechanism, Algorithmic Diversity, Defense-in-Depth, Key Exchange Protocol.

---

## 1. Introduction

The conclusion of the NIST Post-Quantum Cryptography (PQC) standardization process marks the beginning of a global cryptographic migration. While the selected standards, primarily based on structured lattices, offer strong security guarantees against known quantum algorithms, the history of cryptography teaches us to be wary of placing absolute trust in a single family of mathematical assumptions. A future theoretical or practical breakthrough could potentially lead to a systemic failure of an entire class of primitives.

Standard hybrid key exchange protocols mitigate this risk by combining a classical primitive (e.g., ECDH) with a single PQC primitive (e.g., a lattice-based KEM). This ensures that the protocol remains secure as long as at least one of the two components is secure. While this is a significant improvement, it still presents a single point of failure for quantum resistance. If, for instance, a flaw were discovered in the mathematical foundations of lattice-based cryptography, such a hybrid scheme would offer no more quantum resistance than its classical component.

For systems requiring exceptionally high assurance and long-term confidentiality—such as critical infrastructure, national security communications, or archival data—a more conservative approach is warranted. This paper introduces TRI-CROWN, a protocol that extends the hybrid principle to its logical conclusion by incorporating multiple, mathematically distinct post-quantum primitives.

TRI-CROWN is a triple-hybrid KEM that constructs a shared secret from three primitives representing three distinct eras and families of cryptography:

1. **Classical (Elliptic-Curve):** X25519, for its proven security, high performance, and deep ecosystem integration.
2. **Post-Quantum (Lattice-Based):** ML-KEM, the primary NIST standard, representing the state-of-the-art in efficient PQC.
3. **Post-Quantum (Code-Based):** Classic McEliece, a long-standing and trusted PQC candidate with security based on a completely different hardness assumption from lattices.

By composing these three, TRI-CROWN is designed to be "anti-brittle." Its security is not tied to the continued viability of any single assumption. We present the protocol's formal construction, its key schedule designed for forward secrecy and key commitment, and a detailed security analysis.

## 2. Preliminaries

Our protocol is constructed from the following standard cryptographic building blocks:

* **Key Encapsulation Mechanism (KEM):** A set of three algorithms: `KeyGen`, `Encaps`, and `Decaps`. A KEM must provide IND-CCA2 security.
* **Key Derivation Function (KDF):** We use HKDF, specified in RFC 5869, which consists of two phases: `HKDF-Extract` and `HKDF-Expand`.
* **Cryptographic Hash Function:** A collision-resistant hash function, such as SHA3-512.

The specific primitives used in the TRI-CROWN construction are:

* **KEM_ECC:** X25519 Diffie-Hellman function.
* **KEM_Lattice:** ML-KEM-1024, targeting NIST Level 5 security.
* **KEM_Code:** Classic McEliece 6960119, targeting NIST Level 5 security.

## 3. The TRI-CROWN Protocol Specification

TRI-CROWN establishes an authenticated shared secret between an Initiator (Alice) and a Responder (Bob). We assume Bob possesses long-term public keys for all three cryptographic suites.

### 3.1. Handshake and Key Encapsulation

1. **Initialization:** Alice and Bob initialize a transcript hash context, `H_trans = HASH_INIT()`. They hash a domain separation tag and any pre-agreed upon context information.
2. **Initiator's Operation (Alice):**
   a. Alice fetches Bob's public keys: `pk_B_ECC`, `pk_B_Lattice`, `pk_B_Code`.
   b. Alice generates an ephemeral key pair for the ECC component:
      (`epk_A_ECC`, `esk_A_ECC`) ← `KEM_ECC.KeyGen()`
   c. Alice performs three separate key encapsulations:
      i. `ss_ECC` ← `KEM_ECC.DH(esk_A_ECC, pk_B_ECC)`
      ii. (`ct_Lattice`, `ss_Lattice`) ← `KEM_Lattice.Encaps(pk_B_Lattice)`
      iii. (`ct_Code`, `ss_Code`) ← `KEM_Code.Encaps(pk_B_Code)`
   d. Alice updates the transcript with all public information exchanged:
      `H_trans.update(pk_B_ECC || pk_B_Lattice || pk_B_Code)`
      `H_trans.update(epk_A_ECC || ct_Lattice || ct_Code)`
   e. Alice sends the message (`epk_A_ECC`, `ct_Lattice`, `ct_Code`) to Bob.
3. **Responder's Operation (Bob):**
   a. Upon receiving the message, Bob updates his transcript with the same public information.
   b. Bob uses his secret keys (`sk_B_ECC`, `sk_B_Lattice`, `sk_B_Code`) to perform three decapsulations:
      i. `ss_ECC` ← `KEM_ECC.DH(sk_B_ECC, epk_A_ECC)`
      ii. `ss_Lattice` ← `KEM_Lattice.Decaps(sk_B_Lattice, ct_Lattice)`
      iii. `ss_Code` ← `KEM_Code.Decaps(sk_B_Code, ct_Code)`
4. **Shared Secret Combination:** Both parties now possess the same three shared secrets. They combine them via concatenation to form a single Initial Keying Material (IKM):
   `IKM = ss_ECC || ss_Lattice || ss_Code`

### 3.2. Key Schedule

The key schedule uses HKDF to derive session keys from the IKM, binding them to the context of the entire handshake.

1. **Extraction:** The finalized transcript hash is used as the salt to provide key commitment.
   `salt = H_trans.final()`
   `PRK = HKDF-Extract(salt, IKM)`
2. **Expansion:** A master secret is derived, from which all subsequent keys are generated. This structure supports ratcheting for forward and post-compromise security.
   `master_secret = HKDF-Expand(PRK, "tri-crown-master", L_master)`
   `traffic_key_send = HKDF-Expand(master_secret, "send_key", L_key)`
   `traffic_key_recv = HKDF-Expand(master_secret, "recv_key", L_key)`

## 4. Security Analysis

The design of TRI-CROWN is intentionally conservative, prioritizing security and resilience over performance.

* **Hybrid Security:** The security of the derived `master_secret` relies on the secrecy of the `IKM`. An adversary can only compute the `IKM` if they can obtain all three constituent shared secrets: `ss_ECC`, `ss_Lattice`, and `ss_Code`. So long as any one of the three KEMs remains unbroken by the adversary, the `IKM` remains computationally indistinguishable from a random string.
* **Algorithmic Diversity:** This is the core security contribution of TRI-CROWN. The protocol is resilient not just to the threat of a quantum computer (which is handled by both ML-KEM and McEliece), but also to a fundamental cryptanalytic breakthrough against an entire family of PQC algorithms. For example:
  * If a flaw is discovered rendering *all* lattice-based schemes insecure, the protocol's security gracefully degrades to a dual-hybrid scheme of X25519 and Classic McEliece.
  * Similarly, a break in code-based crypto would still leave a secure dual-hybrid of X25519 and ML-KEM.
  This provides a level of assurance that is not achievable with standard classical+PQC hybrid models.
* **Key Commitment:** By including all public keys and ciphertexts in the transcript hash, and using this hash as the KDF salt, the protocol cryptographically binds the derived session keys to the full context of the handshake. This prevents attacks where an adversary might manipulate the exchange to make two parties derive the same key from different session contexts.
* **Forward Secrecy:** The use of an ephemeral key for the ECC component ensures that a compromise of the responder's long-term keys does not compromise past session keys. Full forward secrecy is achieved by having both parties use ephemeral keys for all primitives, which is a straightforward extension of this core protocol.

## 5. Discussion and Future Work

The primary trade-offs of the TRI-CROWN approach are increased computational cost and bandwidth overhead. The three encaps/decaps operations are more expensive than a standard hybrid handshake, and the message containing two PQC ciphertexts is significantly larger. However, for applications where long-term security is paramount and these costs are acceptable, TRI-CROWN offers a compelling security posture.

Future work includes:

1. A formal security proof of the protocol construction in a standard cryptographic model.
2. Performance benchmarking on various platforms, from servers to embedded devices, to quantify the overhead.
3. Developing a side-channel resistant implementation of the full, sequential decapsulation process, taking into account potential cross-primitive leakages.

## 6. Conclusion

TRI-CROWN is a conservatively designed hybrid key exchange protocol that provides robust security guarantees against an uncertain cryptanalytic future. By combining three primitives from distinct mathematical families, it achieves deep algorithmic diversity, ensuring resilience even if an entire class of post-quantum algorithms is broken. This makes it a suitable candidate for securing communications and data that require confidentiality and integrity for many decades to come.

## 7. References

1. Bernstein, D. J. "Curve25519: New Diffie-Hellman Speed Records." In *PKC 2006*, LNCS 3958, pp. 207–228. Springer, 2006.
2. Bindel, N., et al. "CRYSTALS-Kyber." Submission to the NIST Post-Quantum Cryptography Standardization Process. 2020.
3. Bernstein, D. J., et al. "Classic McEliece." Submission to the NIST Post-Quantum Cryptography Standardization Process. 2020.
4. Krawczyk, H., and Eronen, P. "HMAC-based Extract-and-Expand Key Derivation Function (HKDF)." RFC 5869, May 2010.
5. Göttert, N., et al. "On the Implementation of a KEM-Based Hybrid Key Exchange in TLS." In *ACNS 2020*, LNCS 12146, pp. 485–504. Springer, 2020.
