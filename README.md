# PureMaTH-Ω Reference Notes

## 4.3 Rejection Sampling and Signature Correctness
Rejection sampling is the cornerstone of the PureSign-Ω security proof. Its role is to ensure that the distribution of the final output signature $\sigma = (c, z)$ is statistically independent of the secret key $(s_1, s_2)$. Without the rejection step, the distribution of $z = y + c s_1$ would leak information about $s_1$, enabling attackers to mount statistical attacks across many observed signatures. The rejection filter only accepts candidates whose coefficients fall within the publicly known bounds $\gamma_1$ and $\gamma_2$, striking a balance between efficient termination and strong security guarantees.

## 4.4 Serialization of Signatures
The signature $\sigma$ is serialized as a byte string composed of the encoded challenge polynomial $c$ and the signature vector $z$. Helper functions `encode_sig` and `decode_sig` perform canonical serialization and deserialization, compressing $c$ by exploiting its sparse structure and encoding each polynomial that forms $z$.

## Section 5: Security Posture and Implementation Safeguards
A cryptographic implementation is only as strong as its weakest link. The PureMaTH-Ω suite therefore emphasizes constant-time execution, secure randomness, robust error handling, and zeroization of sensitive data.

### 5.1 Side-Channel Resistance: The Imperative of Constant-Time Execution
Side-channel attacks exploit implementation leakage, often via timing differences. Any operations on secret data must run in constant time.

#### 5.1.1 The Rejection Sampling Vulnerability
The naive `while True` rejection sampling loop leaks timing information tied to $(s_1, s_2)$ and the random vector $y$. Early exits inside `check_norm` exacerbate the risk. A constant-time implementation replaces the unbounded loop with a loop running for a fixed maximum number of iterations and uses masking to select the first valid candidate without branching.

```python
MAX_ITERATIONS = 10
found_mask = 0
sig_c = Polynomial()
sig_z = [Polynomial() for _ in range(self.k)]

for i in range(MAX_ITERATIONS):
    # ... generate y, w, c, and z ...
    reject_candidate = check_norm_ct(z, self.gamma1)
    reject_candidate |= check_norm_ct(w_minus_cs2, self.gamma2)
    accept_mask = 1 - min(1, reject_candidate)
    select_mask = accept_mask & (1 - found_mask)
    # Conditionally select the first valid signature via masking
    found_mask |= select_mask

if not found_mask:
    raise RuntimeError("Failed to generate a signature within MAX_ITERATIONS")

return encode_sig(sig_c, sig_z, self.params)
```

#### 5.1.2 Other Potential Timing Leaks
The `decaps` function must compare the received value `v` with the recomputed `v'` in constant time. Early termination in string comparison leaks positional information, so the function accumulates differences via bitwise operations instead.

### 5.2 Cryptographic Hygiene and Best Practices
* **Secure Randomness** – All randomness should come from a CSPRNG (for example, Python’s `secrets` module) rather than the insecure `random` module.
* **Robust Error Handling** – Avoid returning distinguishable error codes that could form an oracle for attackers. `decaps` should always output a byte string of the correct length.
* **Zeroization of Sensitive Data** – Sensitive material must be cleared from memory once it is no longer needed. Languages with manual memory management (e.g., C or Rust) are often used for this level of control.

### 5.3 Validation and Test Vectors
Known Answer Tests (KATs) verify correctness across KEM/DSA key generation, encapsulation/decapsulation, and sign/verify operations for every parameter set. They provide regression safety and interoperability validation.

## Section 6: API Reference and Practical Usage Guide
The API exposes `PureKEM` and `PureSign` classes, each initialized with a parameter set name.

| Module | Function Signature | Description | Return Value |
| --- | --- | --- | --- |
| `kem` | `keygen(params: str) -> (bytes, bytes)` | Generate a KEM key pair | `(public_key, secret_key)` |
| `kem` | `encaps(pk: bytes) -> (bytes, bytes)` | Encapsulate a shared secret for a public key | `(ciphertext, shared_secret)` |
| `kem` | `decaps(ct: bytes, sk: bytes) -> bytes` | Decapsulate a ciphertext | `shared_secret` |
| `dsa` | `keygen(params: str) -> (bytes, bytes)` | Generate a DSA key pair | `(public_key, secret_key)` |
| `dsa` | `sign(sk: bytes, msg: bytes) -> bytes` | Sign a message | `signature` |
| `dsa` | `verify(pk: bytes, msg: bytes, sig: bytes) -> bool` | Verify a signature | `True`/`False` |

### 6.2 Code Examples
#### KEM Workflow (`kem_example.py`)
```python
from kem import PureKEM

params_name = 'PureMaTH-Omega-128'
kem_instance = PureKEM(params_name)

alice_pk, alice_sk = kem_instance.keygen()
ciphertext, bob_shared_secret = kem_instance.encaps(alice_pk)
alice_shared_secret = kem_instance.decaps(ciphertext, alice_sk)

assert alice_shared_secret == bob_shared_secret

tampered_ciphertext = bytearray(ciphertext)
tampered_ciphertext[0] ^= 0xFF
failed_secret = kem_instance.decaps(bytes(tampered_ciphertext), alice_sk)
assert failed_secret != alice_shared_secret
```

#### DSA Workflow (`dsa_example.py`)
```python
from dsa import PureSign

params_name = 'PureMaTH-Omega-128'
dsa_instance = PureSign(params_name)

vendor_pk, vendor_sk = dsa_instance.keygen()
message = b"This is the content of the software update v1.2.3"
signature = dsa_instance.sign(vendor_sk, message)
assert dsa_instance.verify(vendor_pk, message, signature)

tampered_message = b"This is the content of the malicious update v1.2.3"
assert not dsa_instance.verify(vendor_pk, tampered_message, signature)
```

### 6.3 Conclusion and Future Work
The reference implementation prioritizes clarity and correctness while suggesting future optimizations such as implementing performance-critical routines in C or Rust and exploring hardware acceleration for polynomial arithmetic.

## Section 1: The Architecture of Computation: Formal Languages and the Chomsky Hierarchy
Formal grammars describe how strings over a finite alphabet are generated. The Chomsky Hierarchy orders these grammars by expressive power—from regular (Type-3) to unrestricted (Type-0)—and correlates each with the automaton needed to recognize the corresponding language class.

## Section 2: A Taxonomy of Abstract Machines
Each grammar class maps to a machine model: finite-state machines (Type-3), pushdown automata (Type-2), linear-bounded automata (Type-1), and Turing machines (Type-0). Their power is defined by memory structure, from memoryless state machines to the infinite tape of the Turing machine.

## Section 3: The Universal Boundary
The Church-Turing thesis equates "effective computability" with Turing-computable functions. Its acceptance enables proofs of undecidability, such as the halting problem, demonstrating problems no algorithm can solve.

## Section 4: Hilbert's Tenth Problem
Hilbert sought a universal process to determine whether Diophantine equations have integer solutions. The MRDP theorem equated Diophantine sets with recursively enumerable sets, proving that no such algorithm exists and linking number theory with computability.

## Section 5: The Realm of the Solvable
Even within computable problems, complexity varies widely. Greedy algorithms like Kruskal’s MST and Dijkstra’s shortest path exploit structure for efficiency, while NP-complete problems such as Hamiltonian path lack known efficient solutions.

## Section 6: The Logical Bedrock
Boolean algebra underpins digital logic. Tools such as Karnaugh maps simplify Boolean expressions, while bitwise operations—especially XOR—provide reversible, information-preserving primitives crucial for cryptographic implementations.

## Section 7: Computation in Practice
Modern cryptography leverages modular arithmetic to create one-way functions. Cryptographic hash functions like SHA-256 employ bitwise operations, modular addition, and diffusion to deliver deterministic yet unpredictable outputs that satisfy properties such as collision resistance and the avalanche effect.

## Conclusion
From formal language theory to post-quantum cryptography, PureMaTH-Ω demonstrates how theoretical foundations inform practical security engineering. The suite’s emphasis on constant-time implementations, cryptographic hygiene, and comprehensive validation aligns with best practices for robust, post-quantum-ready systems.
