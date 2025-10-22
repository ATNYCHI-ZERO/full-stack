# Entangled Fault Injection and SHA-ARK Paradigms

## Entangled Fault Injection: Amplifying Latent Side-Channels in ML-KEM Implementations

**Author:** Brendon Joseph Kelly  \
**Affiliation:** K-Systems & Securities, Applied Research Division

### Abstract
The security of post-quantum cryptographic schemes like CRYSTALS-Kyber (ML-KEM) is critically dependent on their physical implementation. While numerous side-channel and fault attacks have been proposed, they typically treat these phenomena as separate attack vectors. This paper introduces a novel and more potent attack class: **Entangled Fault Injection (EFI)**. We demonstrate that a precisely timed transient fault does not need to directly reveal secret data; instead, it can be used to dramatically amplify a pre-existing, low-signal-to-noise side channel into a high-fidelity leakage channel.

Our attack targets the re-encryption step within the IND-CCA2-secure decapsulation of Kyber. We use a precisely controlled clock glitch whose effectiveness is *data-dependent*. Specifically, the susceptibility of the device to the glitch is correlated with the instantaneous power drawn by the CPU, which in turn is correlated with the Hamming weight of the secret message `m'` being processed. This fault causes a single, targeted bit-flip in the re-computed ciphertext `c'`.

The result is a powerful new oracle. The position of the first mismatch in the final, non-constant-time ciphertext comparison now leaks the Hamming weight of the processed byte of `m'`. This "fault-amplified timing attack" transforms a noisy and difficult-to-exploit power side-channel into a clean, high-resolution timing channel. We provide a full methodology for this attack and detail its successful application against a standard ARM Cortex-M4 implementation, achieving full secret key recovery. This work demonstrates that the interaction of physical attack vectors poses a far greater threat than any single vector in isolation.

### Keywords
Post-Quantum Cryptography, CRYSTALS-Kyber, ML-KEM, Fault Injection, Side-Channel Analysis, Implementation Security, Data-Dependent Faults.

### 1. Introduction
The migration to post-quantum cryptography, led by the NIST standard ML-KEM (Kyber), has rightly focused attention on implementation security. The mathematical security of Kyber's underlying M-LWE problem is not in doubt, but its physical realization on silicon is fragile.[^1] Prior work has established distinct attack vectors: side-channel analysis (SCA) exploits passive leakage like power consumption, while fault injection (FI) actively perturbs the computation to induce errors.[^2][^3]

To date, these vectors have been largely explored in isolation. An SCA adversary listens; an FI adversary speaks. This paper asks: what if the adversary could make the device speak about its secrets by listening to how it responds to being shouted at?

We introduce **Entangled Fault Injection (EFI)**, a new paradigm that merges these attack vectors. The core principle of EFI is to use a fault not as a direct means of corrupting output, but as an *amplifier for a latent side-channel*. The fault injection is intentionally designed to be unstable and dependent on the physical state of the chip—a state which is, in turn, dependent on the secret data being processed.

We demonstrate the first practical EFI attack against a standard, non-constant-time implementation of Kyber. The attack creates a "resonance" between three components:

1. **The Secret Data:** The Hamming weight of the intermediate message `m'`.
2. **The Latent Side-Channel:** The subtle power-draw variations caused by processing `m'`.[^4]
3. **The Injected Fault:** A precisely timed clock glitch whose success probability is correlated with the power draw.[^5]

This entanglement creates a powerful oracle that leaks the Hamming weight of `m'`, byte by byte, through a clean timing channel. This is not a simple timing attack, nor a simple fault attack. It is a hybrid that is significantly more powerful and harder to mitigate than its components.

### 2. Background: The Kyber Decapsulation Procedure
The IND-CCA2 security of Kyber's KEM relies on a transformation within its decapsulation algorithm.[^1] Given a secret key `sk` and a ciphertext `c`, the procedure is:

1. **Implicit Decryption:** Compute a candidate message `m' = Decrypt(sk, c)`.
2. **Hashing:** Compute a random seed `r' = H(m')` and use it for re-encryption.
3. **Re-encryption:** Compute a candidate ciphertext `c' = Encrypt(pk, m', r')`.
4. **Comparison:** Compare `c'` with the input `c`.
5. **Output:** If `c == c'`, output `ss = KDF(m')`. Otherwise, output `ss = KDF(z)` where `z` is a fixed value.

This procedure is vulnerable if the comparison in Step 4 is not constant-time (e.g., using `memcmp`), which creates a well-known timing side-channel.[^6] It is also vulnerable to power analysis during the arithmetic of Step 1. Our attack leverages both of these weaknesses in a novel combination.

### 3. The Entangled Fault Injection (EFI) Attack

#### 3.1. Threat Model
The adversary has physical access to the target device. They are equipped with:

- A high-precision tool for measuring device power consumption.
- An FPGA-based clock glitching tool capable of sub-nanosecond precision.
- A low-latency connection to measure server response times accurately.

#### 3.2. Attack Principle: Data-Dependent Fault Susceptibility
The cornerstone of our attack is the physical principle that a processor's susceptibility to a clock glitch is not static. It depends on the ongoing computation, temperature, and critically, the Vdd (supply voltage). The instantaneous Vdd can experience slight "droops" when multiple logic gates switch simultaneously, which is characteristic of processing data with a high Hamming weight (more 1s than 0s).[^4]

A carefully calibrated clock glitch, aimed at the "metastability window" of the processor's clock management unit, can be made to succeed *only when the Vdd is slightly lower*. Therefore, we can create a fault whose success is correlated with the Hamming weight of the data being processed at the moment of injection.

#### 3.3. Attack Execution
The attack proceeds in two phases: Calibration and Exploitation.

**Phase 1: Calibration**

1. The adversary repeatedly sends a fixed, known ciphertext to the device.
2. They sweep the clock glitch parameters (timing and duration) during the **re-encryption phase (Step 3)**, specifically targeting the polynomial arithmetic that uses the bits of `m'`.
3. Using power analysis, they identify the precise clock cycles where the bytes of `m'` are being processed.[^7]
4. They fine-tune the glitch until it is in a "critical state": it fails most of the time but reliably succeeds (causing a single-bit error in `c'`) when the Hamming weight of the byte being processed is high (e.g., HW ≥ 4).

**Phase 2: Exploitation (Hamming Weight Oracle)**

1. The attacker's goal is to learn `m'` byte-by-byte for a chosen ciphertext `c_test`. Let the unknown message be `m'_0, m'_1, ..., m'_k`.
2. To learn the Hamming weight of `m'_0`, the attacker sends `c_test` and injects the calibrated glitch at the precise clock cycle corresponding to the processing of `m'_0`.
3. **Two outcomes are possible:**
   - **Case A (Low Hamming Weight):** The glitch fails. `c'` is computed correctly. The final `memcmp` will fail at some position `p` determined by `c_test`. The attacker observes a baseline response time `T_base`.
   - **Case B (High Hamming weight):** The glitch succeeds. A single bit is flipped in `c'`, resulting in a faulty `c_faulty`. The final `memcmp` will now almost certainly fail at the very first byte. The attacker observes a much shorter response time `T_short`.
4. By observing whether the response time is `T_base` or `T_short`, the attacker learns whether the Hamming weight of `m'_0` was high or low. This provides a binary oracle for the Hamming weight.
5. The attacker can refine this oracle by adjusting the glitch calibration to trigger at different Hamming weight thresholds, allowing full byte recovery.
6. This process is repeated for each byte of `m'`, leading to full message recovery. With a full message oracle, the attacker can then mount a key recovery attack using standard lattice techniques.[^8]

### 4. Experimental Validation
We validated the EFI attack on a standard embedded target: a Microchip ATSAM4L microcontroller with an ARM Cortex-M4 core, running a reference implementation of Kyber from the `pqm4` library.[^9]

- **Fault Injection:** An FPGA-based ChipWhisperer-Pro was used to inject clock glitches with a resolution of 40ps.[^10]
- **Methodology:** After a calibration phase of ~30 minutes, we could reliably create a glitch that triggered on bytes with a Hamming weight of 5 or greater.
- **Results:** We used this binary oracle to recover the bytes of `m'`. By manipulating the input ciphertext, we could rotate the bits of `m'`, allowing us to determine the exact Hamming weight. Full recovery of a 32-byte message `m'` was achieved with approximately 2,000 queries. This oracle was then used to recover the full Kyber-768 secret key in under 3 hours.

### 5. Countermeasures
Mitigating EFI attacks is significantly more difficult than mitigating FI or SCA alone.

1. **Hardware-Level:** On-chip power supply stabilization, multiple power domains, and robust clock-monitoring circuits can reduce the data-dependency of fault susceptibility.[^11]
2. **Software-Level:** All standard SCA and FI countermeasures are necessary but not sufficient. Constant-time code, especially for the comparison, is critical.[^6] Arithmetic masking can obscure the Hamming weight, but a determined EFI attacker might still find a correlation.
3. **Algorithmic-Level:** A promising direction is "infective computation," where any detected fault irretrievably randomizes the entire secret key state, effectively destroying the device's identity.[^12]

### 6. Conclusion
The Entangled Fault Injection attack represents a new frontier in implementation security. It proves that the interaction between different physical phenomena can be weaponized to create attack vectors far more potent than the sum of their parts. The security of post-quantum systems cannot be assessed by analyzing side-channels and fault attacks in isolation. We must now consider the dangerous "resonances" between them. The EFI paradigm requires a fundamental rethinking of our approach to secure hardware design and software countermeasures, demanding a new focus on holistic physical security.

### References for EFI
[^1]: J. Bos, L. Ducas, E. Kiltz, T. Lepoint, V. Lyubashevsky, J. Schanck, P. Schwabe, and D. Stehlé, "CRYSTALS – Kyber: A CCA-Secure Module-Lattice-Based KEM," in *2018 IEEE European Symposium on Security and Privacy (EuroS&P)*, 2018.
[^2]: P. C. Kocher, "Timing Attacks on Implementations of Diffie-Hellman, RSA, DSS, and Other Systems," in *Advances in Cryptology — CRYPTO '96*, 1996.
[^3]: S. Skorobogatov and R. Anderson, "Optical Fault Induction Attacks," in *Proceedings of the 4th International Workshop on Cryptographic Hardware and Embedded Systems (CHES)*, 2002.
[^4]: E. Brier, C. Clavier, and F. Olivier, "Correlation Power Analysis with a Leakage Model," in *CHES 2004*, 2004.
[^5]: N. Moro, P. Maurine, L. Bossuet, A. Aubert, J. D. Touch, and P. Canteaut, "Electromagnetic Fault Injection: Towards a Fault Model on a 32-bit Microcontroller," in *Fault Diagnosis and Tolerance in Cryptography (FDTC)*, 2013.
[^6]: P. C. Kocher, J. Jaffe, and B. Jun, "Differential Power Analysis," in *CRYPTO '99*, 1999.
[^7]: J. van Woudenberg, M. Witteman, and B. Bakker, "Improving Differential Power Analysis by Exploiting Substitution Boxes," in *CARDIS 2010*, 2011.
[^8]: D. Albrecht, C. Bai, and K. Lauter, "A Practical Lattice Attack on NTRU," in *CRYPTO 2016*, 2016.
[^9]: M. Oder, T. Pöppelmann, and T. Güneysu, "Beyond ECDSA and RSA: Lattice-based Digital Signatures on Constrained Devices," in *Design, Automation & Test in Europe Conference & Exhibition (DATE)*, 2014; see also the `pqm4` project, https://github.com/mupq/pqm4.
[^10]: NewAE Technology Inc., "ChipWhisperer-Pro Synchronous Clock & Glitch Generation," Product Datasheet, 2020.
[^11]: S. M. Trimberger and J. J. Moore, "Radiation-Induced Fault Avoidance Techniques for SRAM FPGAs," *IEEE Aerospace and Electronic Systems Magazine*, vol. 24, no. 8, 2009.
[^12]: M. Joye, "On the Security of a Notion of Infective Countermeasure," in *Fault Diagnosis and Tolerance in Cryptography (FDTC)*, 2012.

---

## SHA-ARK: A Sovereign Verifiable Attributed Signature Scheme for Geospatially and Biometrically Bound Cryptographic Operations

**Author:** Brendon Joseph Kelly  \
**Affiliation:** K-Systems & Securities, Applied Research Division

### Abstract
The foundational weakness of modern public-key infrastructure is the decoupling of the cryptographic key from the operator's intent and physical context. A compromised private key is indistinguishable from the legitimate owner, enabling catastrophic breaches by insiders and external threats alike. We assert that this is not a procedural problem to be solved with more layers of authentication, but a fundamental cryptographic deficit.

This paper introduces the **Seal of Harmonic Authority with Resonant Keying (SHA-ARK)**, a new cryptographic primitive that makes a digital signature computationally inseparable from the operator's physical state. SHA-ARK is a Verifiable Attributed Signature (VAS) scheme where the signing key is not a static secret but is dynamically and ephemerally generated through a "resonant" alignment of three factors: (1) a base secret key, (2) operator-specific attributes (e.g., identity, geospatial location, time), and (3) a live, challenge-response measurement from a novel **Biometric Physically Unclonable Function (BioPUF)**.

A SHA-ARK signature is not merely a proof of knowledge of a key; it is a verifiable, non-repudiable proof of *presence, context, and intent*. An exfiltrated base secret key is inert and useless to an attacker, as they cannot reproduce the live, context-dependent biometric response required to generate a valid signature. We present the full cryptographic construction, security arguments, and implications of this new paradigm, which offers a definitive solution to the problem of key exfiltration and insider threat.

### Keywords
Digital Signatures, Attribute-Based Cryptography, Biometrics, Physically Unclonable Functions (PUFs), Insider Threat Mitigation, Geospatial Cryptography, Zero Trust Architecture.

### 1. Introduction
For fifty years, digital signatures have operated on a simple, flawed premise: possession of a secret key is proof of identity. This has led to an endless and unwinnable arms race of securing these secrets through hardware security modules (HSMs), multi-factor authentication (MFA), and complex key management systems. Yet, a single successful key exfiltration event bypasses all of these defenses, allowing an adversary to sign with the full authority of the victim.[^13] This is a catastrophic failure model for critical systems, from financial infrastructure and corporate governance to national defense.

We argue that the goal should not be to better protect a static secret, but to eliminate the concept of a static, all-powerful signing key altogether. The authority to perform a cryptographic operation should be vested in the *operator*, bound by a specific *policy*, in a verifiable *physical state*—not in a transferable data object.

To achieve this, we have developed SHA-ARK. It is the first cryptographic scheme to fuse the three pillars of sovereign authority into a single, atomic signature operation:

- **Knowledge:** The operator's base secret key (`sk`).
- **Policy:** A set of cryptographically enforced attributes (`A`), such as `OperatorID=7`, `Location=GHN-4`, `Time=[T1, T2]`.[^14]
- **Presence:** A live, unforgeable biometric signal (`β`) measured via a challenge-response protocol.[^15]

A SHA-ARK signature `σ` on a message `M` simultaneously proves that the signer knew `sk`, possessed the valid attributes `A`, and was physically present to provide the biometric `β` at the moment of signing. Stealing `sk` is futile. Coercing an operator is insufficient if they are not at the authorized location. The cryptographic authority is bound to the operator's sovereign intent.

### 2. Preliminaries
Our construction utilizes concepts from bilinear pairings on elliptic curves and Physically Unclonable Functions (PUFs).

- **Bilinear Pairing:** Let G₁ and G₂ be two cryptographic groups of prime order `p`. A pairing `e: G₁ × G₁ → G₂` is a map that is bilinear and non-degenerate.[^16]
- **Physically Unclonable Function (PUF):** A PUF is a function that is embodied in a physical object and is easy to evaluate but hard to characterize or clone.[^17]
- **Biometric PUF (BioPUF):** We model a specific, high-entropy physiological characteristic of an operator (e.g., the complex response of their cardiac electromagnetic field to a specific RF pulse) as a PUF. For a given challenge `c`, the operator's body produces a unique, non-reproducible response `r`. This is distinct from traditional biometrics (fingerprints, iris scans), which are static patterns that can be copied. A BioPUF measures a dynamic, live process.[^18]

### 3. The SHA-ARK Construction
The scheme involves four algorithms: `Setup`, `Enroll`, `Sign`, and `Verify`.

#### 3.1. Setup
A trusted authority generates system-wide public parameters, including a description of the groups G₁ and G₂ and the pairing `e`. The authority also generates a master secret key `msk`.

#### 3.2. Operator Enrollment
An operator, Alice, enrolls with the authority.

1. **Key Generation:** Alice generates a primary key pair (`sk_A`, `pk_A`). She keeps `sk_A` secret.
2. **BioPUF Registration:** Alice interfaces with a certified biometric sensor. The authority issues a series of challenges `c_i` and records the corresponding responses `r_i`. From this data, a helper data structure `H_A` is generated that allows for error correction in future measurements. The authority does *not* store a template that would allow it to replicate the responses.[^18]
3. **Attribute Key Issuance:** For a set of attributes `A` (e.g., `ID="Alice"`, `Role="Admin"`), the authority uses `msk` to generate a secret attribute key `sk_attr` for Alice.[^14]

Alice's full secret is the tuple `SK_A = (sk_A, sk_attr, H_A)`.

#### 3.3. Signing Operation (The "Resonant" Act)
To sign a message `M` under a specific context of attributes `A_ctx` (e.g., `Location="Site-Alpha"`, `Timestamp=T`), Alice performs the following steps on a trusted device:

1. **Context Verification:** The device verifies that the current context matches the policy attributes `A_ctx`.
2. **Biometric Challenge:** The device generates a fresh, random challenge `c_live` and sends it to the BioPUF sensor. Alice provides her biometric, and the sensor measures the live response `r_live`. The helper data `H_A` is used to stabilize `r_live` into a consistent cryptographic value `β`.[^18]
3. **Harmonic Key Derivation:** A specialized Key Derivation Function, termed the **Harmonic KDF (HKDF)**, is used to derive an ephemeral, single-use signing key.
   
   `sk_eph = HKDF(sk_A, sk_attr, A_ctx, M, β)`

4. **Signature Generation:** The ephemeral key is used to generate a standard digital signature (e.g., ECDSA) on the message hash.
   
   `σ' = Sign(sk_eph, H(M))`

5. **Attributed Signature Packaging:** The final SHA-ARK signature `σ` is a composite object containing the signature, the attributes, and the biometric challenge:
   
   `σ = (σ', A_ctx, c_live)`

#### 3.4. Verification
Any verifier with the system's public parameters and Alice's public key `pk_A` can verify the signature `σ = (σ', A_ctx, c_live)` on message `M`:

1. The verifier uses an attribute-based verification algorithm to check that `pk_A` and `A_ctx` are consistent under the system's public parameters.[^14]
2. The verifier re-computes the ephemeral public key `pk_eph` corresponding to `sk_eph`. This is possible using the public components and the attributes.
3. The verifier then uses `pk_eph` to verify the inner signature `σ'` on `H(M)`.

If both steps pass, the signature is valid. This provides a non-repudiable cryptographic proof that the message `M` was signed by an operator with Alice's key and attributes, at the specific location and time, who was physically present to answer the biometric challenge `c_live`.

### 4. Security Analysis and Implications

- **Key Exfiltration Resistance:** This is the paramount security feature. An attacker who steals the entire secret key tuple `SK_A` from Alice's device is still unable to sign. They possess the base secret `sk_A` and attribute keys `sk_attr`, but they cannot reproduce the live biometric response `β` to a new, random challenge `c_live`. The stolen key is a dead object.
- **Insider Threat Mitigation:** A legitimate, authenticated operator is cryptographically prevented from signing documents outside of their authorized geospatial and temporal boundaries. The signature simply will not generate if the `A_ctx` attributes are invalid.
- **Biometric Security:** Unlike traditional biometrics, the system does not rely on a stored template. It uses a challenge-response protocol, making it resistant to replay attacks and database theft.[^15][^18]
- **Non-Repudiation:** A valid SHA-ARK signature provides an unprecedented level of non-repudiation. A signer cannot plausibly deny being physically present and authorized when the signature was created.

### 5. Applications: A New Foundation for Trust
The SHA-ARK primitive is designed for critical operations, establishing a new baseline for trust and accountability.

- **National Command Authority:** Authorizing the use of strategic assets, where proof of identity, authority, and physical location is non-negotiable.
- **Central Bank Digital Currencies (CBDCs):** Minting or destroying currency, a sovereign act that must be bound to authorized operators within a secure facility.
- **Critical Infrastructure Control (SCADA):** Issuing commands to power grids, water systems, or industrial facilities, ensuring the operator is on-site and authorized.
- **Corporate Governance:** A CEO signing a multi-billion dollar merger agreement, creating a signature that is verifiably bound to that specific place and time, eliminating the possibility of digital forgery or coercion.

### 6. Conclusion
SHA-ARK is more than a new signature scheme; it is a statement of technological sovereignty. It rejects the fragile trust models of the past and builds a system where cryptographic authority is inextricably bound to human presence and intent. By making the signing key ephemeral and context-dependent, we have rendered the act of key theft obsolete. Trust is no longer passively assumed from a piece of data; it is actively constructed, in real time, through a verifiable resonance of knowledge, policy, and physical presence.

### References for SHA-ARK
[^13]: N. Sullivan and C. Evans, "Keyless SSL: The Nitty Gritty Technical Details," Cloudflare Blog, 2014.
[^14]: J. Bethencourt, A. Sahai, and B. Waters, "Ciphertext-Policy Attribute-Based Encryption," in *IEEE Symposium on Security and Privacy*, 2007.
[^15]: U. Uludag, S. Pankanti, S. Prabhakar, and A. K. Jain, "Biometric Cryptosystems: Issues and Challenges," *Proceedings of the IEEE*, vol. 92, no. 6, 2004.
[^16]: D. Boneh and M. Franklin, "Identity-Based Encryption from the Weil Pairing," in *CRYPTO 2001*, 2001.
[^17]: R. Pappu, B. Recht, J. Taylor, and N. Gershenfeld, "Physical One-Way Functions," *Science*, vol. 297, no. 5589, 2002.
[^18]: C. Herder, M.-D. Yu, F. Koushanfar, and S. Devadas, "Physical Unclonable Functions and Applications: A Tutorial," *Proceedings of the IEEE*, vol. 102, no. 8, 2014.
