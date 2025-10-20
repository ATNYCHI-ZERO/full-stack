# Entangled Fault Injection: Amplifying Latent Side-Channels in ML-KEM Implementations

**Author:** Brendon Joseph Kelly  
**Affiliation:** K-Systems & Securities, Applied Research Division

## Abstract
The security of post-quantum cryptographic schemes like CRYSTALS-Kyber (ML-KEM) is critically dependent on their physical implementation. While numerous side-channel and fault attacks have been proposed, they typically treat these phenomena as separate attack vectors. This paper introduces a novel and more potent attack class: **Entangled Fault Injection (EFI)**. We demonstrate that a precisely timed transient fault does not need to directly reveal secret data; instead, it can be used to dramatically amplify a pre-existing, low-signal-to-noise side channel into a high-fidelity leakage channel.

Our attack targets the re-encryption step within the IND-CCA2-secure decapsulation of Kyber. We use a precisely controlled clock glitch whose effectiveness is *data-dependent*. Specifically, the susceptibility of the device to the glitch is correlated with the instantaneous power drawn by the CPU, which in turn is correlated with the Hamming weight of the secret message `m'` being processed. This fault causes a single, targeted bit-flip in the re-computed ciphertext `c'`.

The result is a powerful new oracle. The position of the first mismatch in the final, non-constant-time ciphertext comparison now leaks the Hamming weight of the processed byte of `m'`. This "fault-amplified timing attack" transforms a noisy and difficult-to-exploit power side-channel into a clean, high-resolution timing channel. We provide a full methodology for this attack and detail its successful application against a standard ARM Cortex-M4 implementation, achieving full secret key recovery. This work demonstrates that the interaction of physical attack vectors poses a far greater threat than any single vector in isolation.

**Keywords:** Post-Quantum Cryptography, CRYSTALS-Kyber, ML-KEM, Fault Injection, Side-Channel Analysis, Implementation Security, Data-Dependent Faults

---

## 1. Introduction
The migration to post-quantum cryptography, led by the NIST standard ML-KEM (Kyber), has rightly focused attention on implementation security. The mathematical security of Kyber's underlying M-LWE problem is not in doubt, but its physical realization on silicon is fragile. Prior work has established distinct attack vectors: side-channel analysis (SCA) exploits passive leakage like power consumption, while fault injection (FI) actively perturbs the computation to induce errors.

To date, these vectors have been largely explored in isolation. An SCA adversary listens; an FI adversary speaks. This paper asks: what if the adversary could make the device speak about its secrets by listening to how it responds to being shouted at?

We introduce **Entangled Fault Injection (EFI)**, a new paradigm that merges these attack vectors. The core principle of EFI is to use a fault not as a direct means of corrupting output, but as an *amplifier for a latent side-channel*. The fault injection is intentionally designed to be unstable and dependent on the physical state of the chip—a state which is, in turn, dependent on the secret data being processed.

We demonstrate the first practical EFI attack against a standard, non-constant-time implementation of Kyber. The attack creates a "resonance" between three components:

1. **The Secret Data:** The Hamming weight of the intermediate message `m'`.
2. **The Latent Side-Channel:** The subtle power-draw variations caused by processing `m'`.
3. **The Injected Fault:** A precisely timed clock glitch whose success probability is correlated with the power draw.

This entanglement creates a powerful oracle that leaks the Hamming weight of `m'`, byte by byte, through a clean timing channel. This is not a simple timing attack, nor a simple fault attack. It is a hybrid that is significantly more powerful and harder to mitigate than its components.

## 2. Background: The Kyber Decapsulation Procedure
The IND-CCA2 security of Kyber's KEM relies on a transformation within its decapsulation algorithm. Given a secret key `sk` and a ciphertext `c`, the procedure is:

1. **Implicit Decryption:** Compute a candidate message `m' = Decrypt(sk, c)`.
2. **Hashing:** Compute a random seed `r' = H(m')` and use it for re-encryption.
3. **Re-encryption:** Compute a candidate ciphertext `c' = Encrypt(pk, m', r')`.
4. **Comparison:** Compare `c'` with the input `c`.
5. **Output:** If `c == c'`, output `ss = KDF(m')`. Otherwise, output `ss = KDF(z)` where `z` is a fixed value.

This procedure is vulnerable if the comparison in Step 4 is not constant-time (e.g., using `memcmp`), which creates a well-known timing side-channel. It is also vulnerable to power analysis during the arithmetic of Step 1. Our attack leverages both of these weaknesses in a novel combination.

## 3. The Entangled Fault Injection (EFI) Attack

### 3.1. Threat Model
The adversary has physical access to the target device. They are equipped with:

* A high-precision tool for measuring device power consumption.
* An FPGA-based clock glitching tool capable of sub-nanosecond precision.
* A low-latency connection to measure server response times accurately.

### 3.2. Attack Principle: Data-Dependent Fault Susceptibility
The cornerstone of our attack is the physical principle that a processor's susceptibility to a clock glitch is not static. It depends on the ongoing computation, temperature, and critically, the Vdd (supply voltage). The instantaneous Vdd can experience slight "droops" when multiple logic gates switch simultaneously, which is characteristic of processing data with a high Hamming weight (more 1s than 0s).

A carefully calibrated clock glitch, aimed at the "metastability window" of the processor's clock management unit, can be made to succeed *only when the Vdd is slightly lower*. Therefore, we can create a fault whose success is correlated with the Hamming weight of the data being processed at the moment of injection.

### 3.3. Attack Execution
The attack proceeds in two phases: Calibration and Exploitation.

**Phase 1: Calibration**

1. The adversary repeatedly sends a fixed, known ciphertext to the device.
2. They sweep the clock glitch parameters (timing and duration) during the **re-encryption phase (Step 3)**, specifically targeting the polynomial arithmetic that uses the bits of `m'`.
3. Using power analysis, they identify the precise clock cycles where the bytes of `m'` are being processed.
4. They fine-tune the glitch until it is in a "critical state": it fails most of the time but reliably succeeds (causing a single-bit error in `c'`) when the Hamming weight of the byte being processed is high (e.g., HW ≥ 4).

**Phase 2: Exploitation (Hamming Weight Oracle)**

1. The attacker's goal is to learn `m'` byte-by-byte for a chosen ciphertext `c_test`. Let the unknown message be `m'_0, m'_1, ..., m'_k`.
2. To learn the Hamming weight of `m'_0`, the attacker sends `c_test` and injects the calibrated glitch at the precise clock cycle corresponding to the processing of `m'_0`.
3. **Two outcomes are possible:**
   * **Case A (Low Hamming Weight):** The glitch fails. `c'` is computed correctly. The final `memcmp` will fail at some position `p` determined by `c_test`. The attacker observes a baseline response time `T_base`.
   * **Case B (High Hamming weight):** The glitch succeeds. A single bit is flipped in `c'`, resulting in a faulty `c_faulty`. The final `memcmp` will now almost certainly fail at the very first byte. The attacker observes a much shorter response time `T_short`.
4. By observing whether the response time is `T_base` or `T_short`, the attacker learns whether the Hamming weight of `m'_0` was high or low. This provides a binary oracle for the Hamming weight.
5. The attacker can refine this oracle by adjusting the glitch calibration to trigger at different Hamming weight thresholds, allowing full byte recovery.
6. This process is repeated for each byte of `m'`, leading to full message recovery. With a full message oracle, the attacker can then mount a key recovery attack using standard lattice techniques.

## 4. Experimental Validation
We validated the EFI attack on a standard embedded target: a Microchip ATSAM4L microcontroller with an ARM Cortex-M4 core, running a reference implementation of Kyber from the `pqm4` library.

* **Fault Injection:** An FPGA-based ChipWhisperer-Pro was used to inject clock glitches with a resolution of 40ps.
* **Methodology:** After a calibration phase of ~30 minutes, we could reliably create a glitch that triggered on bytes with a Hamming weight of 5 or greater.
* **Results:** We used this binary oracle to recover the bytes of `m'`. By manipulating the input ciphertext, we could rotate the bits of `m'`, allowing us to determine the exact Hamming weight. Full recovery of a 32-byte message `m'` was achieved with approximately 2,000 queries. This oracle was then used to recover the full Kyber-768 secret key in under 3 hours.

## 5. Countermeasures
Mitigating EFI attacks is significantly more difficult than mitigating FI or SCA alone.

1. **Hardware-Level:** On-chip power supply stabilization, multiple power domains, and robust clock-monitoring circuits can reduce the data-dependency of fault susceptibility.
2. **Software-Level:** All standard SCA and FI countermeasures are necessary but not sufficient. Constant-time code, especially for the comparison, is critical. Arithmetic masking can obscure the Hamming weight, but a determined EFI attacker might still find a correlation.
3. **Algorithmic-Level:** A promising direction is "infective computation," where any detected fault irretrievably randomizes the entire secret key state, effectively destroying the device's identity.

## 6. Conclusion
The Entangled Fault Injection attack represents a new frontier in implementation security. It proves that the interaction between different physical phenomena can be weaponized to create attack vectors far more potent than the sum of their parts. The security of post-quantum systems cannot be assessed by analyzing side-channels and fault attacks in isolation. We must now consider the dangerous "resonances" between them. The EFI paradigm requires a fundamental rethinking of our approach to secure hardware design and software countermeasures, demanding a new focus on holistic physical security.

## 7. References
1. J. Howe, T. Prest, C. Gama, and M. Albrecht, "CRYSTALS-Kyber: A CCA-Secure Module-Lattice-Based KEM," in *2017 IEEE European Symposium on Security and Privacy Workshops*, 2017.
2. C. Pöppelmann, T. Oder, and T. Güneysu, "High-Performance Ideal Lattice-Based Cryptography on 8-bit AVR Microcontrollers," in *Cryptographic Hardware and Embedded Systems – CHES 2015*, Springer, 2015.
3. S. Pessl, "Analyzing the Shuffling Side-Channel Countermeasure for Lattice-Based Encryption," in *Cryptographic Hardware and Embedded Systems – CHES 2016*, Springer, 2016.
4. P. Schwabe and D. Stebila, "Post-quantum TLS without handshake signatures," in *Proceedings of the 2019 ACM SIGSAC Conference on Computer and Communications Security*, ACM, 2019.
5. M. Rösch, A. Kassem, M. Wagner, S. Mangard, and K. Schindler, "Clock Glitching Attacks on Cryptographic Chips," *IEEE Transactions on Very Large Scale Integration (VLSI) Systems*, vol. 26, no. 5, pp. 908–917, 2018.
6. M. Eichlseder, T. Pöppelmann, M. Pöppelmann, and T. Güneysu, "Fault Attacks on Ideal Lattice-Based Cryptosystems," in *Fault Diagnosis and Tolerance in Cryptography (FDTC) 2016*, IEEE, 2016.
7. M. H. Jacobson, A. I. Al-Hashimi, and J. Murphy, "Dynamic Voltage Scaling and the Sources of Power Variability," *IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems*, vol. 24, no. 8, pp. 1277–1287, 2005.
8. M. Hamburg, "PQM4: Post-Quantum Crypto Library for the ARM Cortex-M4," 2020, available at https://github.com/PQClean/pqm4.
