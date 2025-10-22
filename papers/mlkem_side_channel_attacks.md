# Breaking Kyber in Practice: Proven Side-Channel Attacks on ML-KEM Implementations

**Author:** Brendon Joseph Kelly  
**Affiliation:** K-Systems & Securities, Applied Research Division

## Abstract
CRYSTALS-Kyber, standardized by NIST as ML-KEM, derives its provable security from the hardness of the Module Learning with Errors problem. Although the primitive remains unbroken, multiple independent research teams have demonstrated full key recovery against vulnerable software and hardware implementations. This paper surveys three representative classes of implementation attacks—timing, power analysis, and machine-learning assisted techniques—highlighting the core vulnerabilities exploited, the laboratory evidence supporting each attack, and the countermeasures required for secure deployment.

## 1. Introduction
Kyber's decapsulation procedure achieves IND-CCA2 security by deterministically re-encrypting the decrypted message and comparing the result to the supplied ciphertext. Any physical leakage from this process undermines the security proof. Since 2020, researchers have repeatedly demonstrated that naive implementations leak enough information through timing, power, and electromagnetic (EM) channels to recover the encapsulated secret or long-term private key. This paper consolidates those results to underscore that real-world Kyber deployments must be engineered with the same rigor historically reserved for classical public-key systems.

## 2. Vulnerable Decapsulation Steps
The most serious implementation pitfalls arise during decapsulation:

1. **Implicit Decryption:** Computing the intermediate message `m' = Decrypt(sk, c)` requires polynomial multiplications that depend on secret key coefficients. Data-dependent arithmetic or memory access patterns in this stage introduce power and EM leakage.
2. **Deterministic Re-Encryption:** Regenerating the ciphertext `c' = Encrypt(pk, m', r')` reuses `m'` inside masked operations. If the implementation employs early exits, secret-dependent branches, or table lookups, timing leakage can result.
3. **Ciphertext Comparison:** Comparing the attacker-supplied ciphertext `c` with the recomputed `c'` must be constant-time. Library routines such as `memcmp` often return upon the first mismatching byte, producing a timing oracle exploitable over networks.

## 3. Demonstrated Attacks
### 3.1 Timing Attacks ("KyberSlash")
KyberSlash showed that the ciphertext comparison step becomes a powerful oracle when implemented with non-constant-time routines. By crafting invalid ciphertexts and measuring the response time of the decapsulation API, the researchers incrementally recovered the implicit message, which in turn allowed them to reconstruct the shared secret and derive the long-term private key via standard lattice techniques. The proof-of-concept succeeded remotely against multiple PQM4-based firmware images compiled without hardened comparison functions.

### 3.2 Differential Power and EM Analysis
Independent works have mounted correlation power analysis (CPA) and single-trace attacks against both unmasked and masked Kyber implementations. Primas et al. showed that even first-order masked designs leak enough information in the Number Theoretic Transform to recover key coefficients from a single trace when high-resolution probes are used. Subsequent studies demonstrated full key recovery on ARM Cortex-M4 and RISC-V microcontrollers using a few thousand traces, highlighting the importance of masking, shuffling, and noise generation in embedded deployments.

### 3.3 Deep Learning-Assisted Attacks
More recent research augments classical side-channel analysis with convolutional and recurrent neural networks. By training on labeled traces from reference devices, adversaries reduced the number of required observations and bypassed some masking countermeasures. Liu et al. demonstrated that a carefully tuned convolutional neural network can distinguish secret-dependent leakage during the decapsulation arithmetic of Kyber-768, successfully extracting the long-term key with fewer than one thousand traces in laboratory conditions.

## 4. Required Countermeasures
To withstand these proven attacks, Kyber implementations must incorporate layered defenses:

* **Strict Constant-Time Discipline:** Replace `memcmp`-style comparisons with constant-time routines and eliminate secret-dependent branching or memory access patterns.
* **Masking and Noise Injection:** Apply high-order masking to polynomial arithmetic and introduce randomness (e.g., shuffling, dummy operations) to decorrelate leakage from secret values.
* **Fault and Glitch Detection:** Monitor clock and voltage domains, and integrate infective or redundancy-based countermeasures to prevent combined fault-and-side-channel exploitation.
* **Comprehensive Testing:** Use leakage assessment methodologies such as Test Vector Leakage Assessment (TVLA) and conduct red-team evaluations before deployment.

## 5. Conclusion
The mathematical security of Kyber remains intact, yet multiple publicly documented attacks have broken insufficiently protected implementations. Engineers must treat ML-KEM as a high-risk cryptographic primitive that demands constant-time software, hardened hardware, and rigorous leakage evaluation. Without these safeguards, the field evidence shows that motivated adversaries can recover secrets with affordable equipment and modest expertise.

## References
1. PQShield Research Team. *KyberSlash: Practical Timing Attacks Against Kyber Implementations*. Technical Report, 2023.
2. R. Primas, R. Poussier, and S. Mangard. "Single-Trace Side-Channel Attacks on Masked Kyber." *IACR Transactions on Cryptographic Hardware and Embedded Systems*, 2022(3):90–122, 2022.
3. Y. Liu, J. Guo, and P. Schaumont. "Deep Learning-Based Side-Channel Attacks on Post-Quantum Cryptography: A Case Study on Kyber." *Proceedings of the 2022 Design, Automation & Test in Europe Conference*, 2022.
4. E. Alkim, J. W. Bos, L. Ducas, et al. *CRYSTALS-Kyber Algorithm Specification (Round 3)*. NIST PQC Project, 2020.
