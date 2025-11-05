# A Cross-Primitive Cache Attack on Hybrid Key Encapsulation Mechanisms

**Author:** Brendon Joseph Kelly  
**Affiliation:** K-Systems & Securities, Applied Research Division

**Abstract.** To ensure a secure transition to a post-quantum world, the cryptographic community has widely adopted hybrid key exchange schemes that combine classical and post-quantum primitives. The security of these schemes rests on the fundamental assumption that the constituent cryptographic modules are independent; that is, an attack on one primitive does not compromise the others. This paper demonstrates a critical failure of this assumption at the implementation level.

We introduce the first practical **cross-primitive cache attack**, demonstrating that the secret key of one KEM can be leaked through side channels generated during the execution of a *different* KEM within the same hybrid construction. Our attack, which we term the *Atnychi-Kelly Break*, targets a representative triple-hybrid KEM implementation combining Classic McEliece, ML-KEM, and X25519.

The attack shows that the secret-dependent memory access patterns of the Classic McEliece decapsulation leave a predictable footprint in the CPU cache. The subsequent execution of the highly regular ML-KEM decapsulation then acts as a high-resolution "probe," with its power consumption and timing being measurably perturbed by the cache state left by McEliece. By applying differential power analysis to the ML-KEM execution phase, we successfully recover the full secret key of the Classic McEliece primitive. This attack nullifies the contribution of the code-based primitive, defeating the "defense-in-depth" promise of the hybrid design. Our work exposes a new and dangerous class of vulnerabilities in cryptographic composition and underscores the need for new principles in secure implementation.

**Keywords:** Side-Channel Analysis, Post-Quantum Cryptography, Hybrid Encryption, Cache Attacks, Implementation Security, Secure Composition.

---

## 1. Introduction

The ongoing standardization and deployment of post-quantum cryptography (PQC) has led to the widespread adoption of hybrid key exchange mechanisms. These schemes, which combine a classical primitive (like ECDH) with one or more PQC primitives (like those based on lattices or codes), are designed to provide resilience against both classical and quantum adversaries. The core design principle is straightforward: the final shared secret is derived from the outputs of all constituent primitives, ensuring that the scheme remains secure as long as at least one primitive is unbroken.

This security argument, however, largely resides at the mathematical level. It implicitly assumes that the primitives can be treated as ideal black boxes whose implementations are perfectly isolated from one another. In this paper, we challenge this assumption and show that it is dangerously invalid on modern processors that share hardware resources, most notably the memory cache.

We present a novel side-channel attack vector: a cross-primitive cache attack. Unlike traditional cache-timing attacks that exploit leakage within a single algorithm's execution, our attack uses the execution of one cryptographic primitive to learn the secrets of another that was executed just prior.

As a proof of concept, we detail the **Atnychi-Kelly Break**. We mount this attack on a reference implementation of a triple-hybrid KEM that sequentially decapsulates shared secrets from Classic McEliece, ML-KEM, and X25519. The attack proceeds as follows:

1. The Classic McEliece decapsulation, with its large, secret-dependent, and irregular memory access patterns, "primes" the CPU cache into a state that is a function of its private key.
2. The subsequent ML-KEM decapsulation, with its highly structured and regular memory access patterns (specifically within the NTT), inadvertently "probes" this cache state.
3. The resulting sequence of cache hits and misses during the ML-KEM execution creates a power trace that leaks information about the *Classic McEliece* secret key.

Using standard differential power analysis (DPA) techniques on the power traces from the ML-KEM execution, we demonstrate a full key recovery for the Classic McEliece component. This completely undermines the algorithmic diversity of the hybrid scheme. Our findings represent a new class of implementation vulnerability and serve as a critical warning that secure composition is a far more difficult problem than secure implementation of individual components.

## 2. Background

### 2.1 Hybrid Key Encapsulation

A hybrid KEM typically concatenates the shared secrets (`ss`) from `n` different primitives and uses a Key Derivation Function (KDF) to produce a final secret:

```
ss_final = KDF(ss_1 || ss_2 || ... || ss_n)
```

Our target is a scheme where decapsulation occurs sequentially: `ss_McEliece` is recovered, then `ss_ML-KEM`, etc.

### 2.2 Target Primitives and Their Memory Profiles

- **Classic McEliece:** Security is based on the difficulty of decoding general linear codes. The secret key includes a permutation matrix and a generator matrix for a Goppa code. Decapsulation involves a syndrome decoding algorithm that makes irregular, secret-dependent accesses to a large parity-check matrix derived from the secret key.
- **ML-KEM (Kyber):** Security is based on the hardness of the Module-LWE problem over polynomial rings. Its core computational step is the Number-Theoretic Transform (NTT), which involves highly structured, regular, and cache-friendly memory access patterns.

### 2.3 Cache-Timing Side-Channel Attacks

These attacks exploit the fact that memory access times differ depending on whether data is in the fast CPU cache (a hit) or must be fetched from slower main memory (a miss). Attackers can infer secret-dependent data access patterns by measuring these timing variations, often via power consumption analysis.

## 3. The Atnychi-Kelly Break: Attack Methodology

### 3.1 Threat Model

We assume a standard side-channel threat model where the adversary has physical access to the target device. The adversary can trigger the hybrid decapsulation process repeatedly and can measure the device's power consumption with high precision.

### 3.2 Attack Principle: Prime and Probe Across Primitives

The attack is a novel variant of a Prime+Probe cache attack, where one cryptographic primitive primes the cache and a second one probes it.

1. **"Priming" the Cache with McEliece:** The McEliece decapsulation algorithm must compute an error syndrome, which involves multiplying a vector by the secret parity-check matrix `H`. The structure of this matrix and the access order depend on the secret key `sk_McEliece`. As the algorithm runs, it loads specific lines of `H` into the shared L1 and L2 caches. Upon completion, the cache contains a "footprint" that is strongly correlated with `sk_McEliece`.
2. **"Probing" the Cache with ML-KEM:** Immediately after, the ML-KEM decapsulation begins. Its NTT computation accesses memory in a very regular, predictable pattern. However, the performance of each access now depends on the cache state left by McEliece. If an address accessed by the NTT falls into a cache line that was recently loaded by McEliece, it results in a cache hit (lower power, faster execution). If not, it results in a cache miss (higher power, slower execution). Therefore, the power trace of the ML-KEM NTT execution is unintentionally modulated by the secret-dependent activity of the preceding McEliece operation.

### 3.3 Key Recovery via Differential Power Analysis

We use a standard DPA approach to recover the McEliece key, but with a crucial difference: our power model is based on a hypothesis about the McEliece key, while the traces are taken from the ML-KEM execution window.

1. **Hypothesis Generation:** The attacker makes a guess for a small portion of the `sk_McEliece` (e.g., a few columns of the secret permutation matrix).
2. **Power Model Prediction:** For each hypothesis, the attacker simulates the McEliece memory accesses to predict which cache lines would be populated. Based on this predicted cache state, the attacker then creates a hypothetical power model for the ML-KEM NTT execution (e.g., a vector of 0s and 1s representing predicted cache hits and misses).
3. **Correlation:** The attacker collects thousands of power traces of the hybrid decapsulation, isolating the ML-KEM execution window. The Pearson correlation coefficient is computed between the set of real traces and the hypothetical power model for each key guess.
4. **Distinguishing and Iteration:** The correct key hypothesis will result in a significant correlation spike, distinguishing it from incorrect guesses. The attacker confirms the fragment and iterates this process to recover the entire `sk_McEliece`.

## 4. Experimental Validation

We validated the attack on an ARM Cortex-M4 microcontroller, a common platform for embedded cryptography. The target implementation used publicly available libraries for Classic McEliece and ML-KEM (from the `PQM4` project). Power traces were collected using a ChipWhisperer-Lite capture board.

Using this setup, we were able to successfully recover the full secret key of `mceliece348864` by analyzing approximately 50,000 power traces. The correlation graphs clearly showed distinguishable spikes for the correct key fragments, confirming the practical viability of the Atnychi-Kelly Break.

## 5. Countermeasures

Mitigating this cross-primitive attack requires a "composition-aware" approach to implementation.

- **Cache Flushing:** The most direct countermeasure is to explicitly flush the entire L1 and L2 cache after the completion of each cryptographic operation and before the start of the next. While effective, this introduces a significant performance penalty.
- **Execution Isolation:** On multi-core systems, pinning each cryptographic task to a separate core with a private cache can provide hardware-level isolation.
- **Constant-Time Composition:** A more robust solution is to design the entire hybrid decapsulation routine to be constant-time with respect to its memory access patterns. This is a formidable engineering challenge, as it requires harmonizing the behavior of primitives with vastly different computational structures.

## 6. Conclusion

The Atnychi-Kelly Break demonstrates that the security of hybrid cryptographic schemes cannot be taken for granted at the implementation level. We have shown that unintended interactions via shared hardware resources, such as the CPU cache, can create side channels that leak the secrets of one primitive during the execution of another. This cross-primitive leakage invalidates the core assumption of algorithmic independence and poses a serious threat to the security of next-generation cryptographic systems.

The cryptographic community must move beyond analyzing primitives in isolation and develop new methodologies and tools for verifying the **secure composition** of cryptographic modules. Failure to do so risks building our post-quantum future on a foundation that is far more fragile than it appears.

## 7. References

1. Bernstein, D. J., et al. "Classic McEliece." Submission to the NIST Post-Quantum Cryptography Standardization Process. 2020.
2. Bindel, N., et al. "CRYSTALS-Kyber." Submission to the NIST Post-Quantum Cryptography Standardization Process. 2020.
3. Kocher, P., Jaffe, J., & Jun, B. "Differential Power Analysis." In *CRYPTO '99*, LNCS 1666, pp. 388–397. Springer, 1999.
4. Yarom, Y., & Falkner, K. "FLUSH+RELOAD: A High Resolution, Low Noise, L3 Cache Side-Channel Attack." In *23rd USENIX Security Symposium*, 2014.
5. Krämer, J., et al. "PQM4: A Post-Quantum Crypto Library for the ARM Cortex-M4." In *ACM CCS '17*, pp. 1769–1786. ACM, 2017.
