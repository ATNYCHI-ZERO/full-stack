# Reference Implementation of the PureMaTH-Ω Cryptographic Suite

## 1. Architectural Overview of the PureMaTH-Ω Suite

### 1.1 Introduction to Post-Quantum Cryptography and PureMaTH-Ω
The advent of large-scale quantum computers poses a fundamental threat to modern digital communications. Cryptographic systems such as RSA and Elliptic Curve Cryptography (ECC) are secure today because they rely on the computational difficulty of integer factorization and discrete logarithm problems. While these problems are hard for classical computers, Shor's algorithm allows a sufficiently powerful quantum computer to solve them efficiently. The need to protect data against quantum adversaries has fueled worldwide research into post-quantum cryptography (PQC).

PQC algorithms are designed for classical computers but rely on problems that are believed to be hard for both classical and quantum attackers. The PureMaTH-Ω suite is a comprehensive, quantum-resistant collection of primitives that provide the essential building blocks for secure communication protocols in a post-quantum era. The suite is composed of two primary components:

- **PureKEM-Ω** – A Key Encapsulation Mechanism (KEM) for establishing shared secrets across insecure channels.
- **PureSign-Ω** – A Digital Signature Algorithm (DSA) for authenticity and integrity of digital data.

Combined, these components deliver the foundation required by protocols such as TLS 1.3, secure software updates, and authenticated communication systems while maintaining security against quantum-capable adversaries.

### 1.2 Design Philosophy: Simplicity and Security
PureMaTH-Ω emphasizes simplicity in its mathematical structure. Both the KEM and the DSA rely on the same Module Learning with Errors (Module-LWE) hardness assumption, enabling significant code reuse for polynomial arithmetic, sampling routines, and other shared building blocks. Security proofs in the Quantum Random Oracle Model (QROM) reduce the suite's security to the difficulty of the underlying Module-LWE problem, establishing a strong theoretical foundation.

The conceptual simplicity of the mathematics does **not** translate to straightforward, secure software. Implementations must guard against side-channel attacks and comply with strict requirements for constant-time execution, rejection sampling, and precise polynomial arithmetic. The reference implementation bridges theory and practice by illustrating how to translate the specification into secure, side-channel-resistant code.

### 1.3 Intended Applications and Scope
PureMaTH-Ω targets the same applications currently relying on public-key cryptography. The KEM supports key exchanges in secure communication protocols such as future TLS releases, VPNs (IPsec), and secure messaging. The DSA is suitable for digital signatures in software updates, certificates, and secure boot processes.

The Python reference implementation prioritizes clarity and fidelity to the white paper, offering a canonical blueprint for developers, auditors, and researchers. High-performance production deployments may use the reference as a guide when implementing optimized versions in languages such as C or Rust.

## 2. Mathematical and Cryptographic Foundations

### 2.1 Algebraic Setting: Polynomial Rings and Modules
PureMaTH-Ω operates over the ring \( R_q = \mathbb{Z}_q[X] / (X^n + 1) \), with prime modulus \( q \) and power-of-two degree \( n \). Elements are polynomials of degree less than \( n \), and operations occur modulo \( X^n + 1 \), enforcing the relation \( X^n \equiv -1 \). Vectors and matrices of these polynomials form modules over \( R_q \), enabling linear algebra operations where scalars are polynomials from \( R_q \).

The chosen modulus facilitates the Number Theoretic Transform (NTT), the finite-field analogue of the FFT, which reduces polynomial multiplication from \( O(n^2) \) to \( O(n \log n) \). Efficient NTT implementations are therefore critical for practical deployments of PureMaTH-Ω.

### 2.2 Source of Hardness: The Module-LWE Problem
The suite's security rests on the Module-LWE problem. Given a uniformly random matrix \( A \in R_q^{k \times k} \) and vector \( t \in R_q^k \), the challenge is to distinguish Module-LWE samples of the form \( t = As + e \) (with small secrets \( s \) and errors \( e \)) from uniform random vectors, or to recover \( s \) from \( (A, t) \). Both tasks are believed to be intractable for polynomial-time adversaries, including quantum computers.

### 2.3 Core Cryptographic Primitives
#### Hashing and Extendable-Output Functions (XOFs)
PureMaTH-Ω adopts SHA-3-based XOFs for domain-separated hashing tasks:

- **G (SHAKE256)** – Derives shared secret keys in the KEM.
- **H (SHAKE256)** – Hashes public keys, ciphertexts, and other values.
- **SHAKE128 XOF** – Expands the seed \( \rho \) into the public matrix \( A \).

#### Sampling from the Centered Binomial Distribution (CBD)
Secret and error polynomials draw coefficients from the centered binomial distribution \( \text{CBD}_\eta \). Each coefficient is generated by summing the differences between pairs of uniformly random bits, yielding small integers centered at zero. Entire polynomials are sampled by repeating the procedure for all \( n \) coefficients.

### 2.4 Security Parameter Sets
PureMaTH-Ω defines parameter sets aligned with NIST PQC security levels I, III, and V, sharing a unified architecture to maximize code reuse. The table below summarizes the parameters:

| Parameter Set | NIST Level | \( k \) | \( n \) | \( q \) | \( \eta \) | \( \gamma_1 \) | \( \gamma_2 \) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PureMaTH-Omega-128 | I | 2 | 256 | 8,380,417 | 3 | \( (q-1)/88 \) | \( 2^{17} \) |
| PureMaTH-Omega-192 | III | 3 | 256 | 8,380,417 | 2 | \( (q-1)/78 \) | \( 2^{19} \) |
| PureMaTH-Omega-256 | V | 4 | 256 | 8,380,417 | 2 | \( (q-1)/60 \) | \( 2^{19} \) |

## 3. PureKEM-Ω: A Reference Implementation

### 3.1 Algorithmic Specification
PureKEM-Ω consists of **KeyGen**, **Encaps**, and **Decaps**. Key generation produces \( (\rho, t) \) and secret vector \( s \); encapsulation regenerates \( A \), samples ephemeral values, and creates ciphertext components \( u \) and \( v \); decapsulation reconstructs \( v' \), compares compressed values in constant time, and derives the shared secret if the ciphertext is valid.

### 3.2 Python Implementation Overview
The reference code illustrates:

- Seed expansion into \( A \) via SHAKE128.
- CBD sampling for secrets and errors.
- NTT-based matrix-vector multiplication for efficiency.
- Serialization through `encode_*`/`decode_*` helpers.
- Constant-time operations in decapsulation to avoid side-channel leaks.

### 3.3 Data Structures and Serialization
Keys and ciphertexts serialize polynomials using little-endian packing:

- **Public key** – Seed \( \rho \) concatenated with encoded \( t \).
- **Secret key** – Encoded vector \( s \).
- **Ciphertext** – Encoded, compressed \( u \) and \( v \).

### 3.4 Compression
Compression reduces bandwidth and supports error reconciliation. Because the difference between \( v \) and \( v' \) remains small for valid ciphertexts, lossy compression ensures matching representations, while invalid ciphertexts fail the comparison.

## 4. PureSign-Ω: A Reference Implementation

### 4.1 Algorithmic Specification
PureSign-Ω uses Fiat-Shamir with Aborts and mirrors the KEM's key generation. The signing algorithm:

1. Decodes the secret key, generates a salt, and hashes the message.
2. Executes a rejection sampling loop:
   - Samples a masking vector \( y \).
   - Computes commitment \( w = Ay \).
   - Derives challenge polynomial \( c \).
   - Computes \( z = y + c s_1 \).
   - Checks \( z \) and \( w - c s_2 \) against bounds \( \gamma_1 \) and \( \gamma_2 \).
3. Encodes \( (c, z) \) as the signature.

Verification recomputes \( w' = Az - ct \) and the challenge hash to confirm validity.

### 4.2 Python Implementation Overview
The reference signer and verifier emphasize:

- Consistent key decoding and matrix regeneration.
- Rejection sampling in the signing loop.
- Constant-time requirements for production implementations, especially within the rejection loop and norm checks.

## 5. Security Considerations
- **Constant-time Execution** – Critical across KEM and DSA operations to mitigate timing side channels.
- **Rejection Sampling** – Must be carefully engineered to avoid leakage via abort patterns.
- **Implementation Fidelity** – Serialization, compression, and polynomial arithmetic must adhere to specification details.

## 6. Implementation Guidance
- Use the Python reference as an authoritative specification.
- For production, re-implement performance-critical routines (NTT, CBD sampling) in optimized languages while preserving constant-time properties.
- Reuse the shared core math module across KEM and DSA implementations to minimize attack surface and streamline auditing.

