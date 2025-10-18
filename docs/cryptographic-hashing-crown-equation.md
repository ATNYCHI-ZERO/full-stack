# White Paper: Cryptographic Hashing as a Method for Verifying the Crown Equation

- **Author:** Brendon Joseph Kelly, K Systems and Securities
- **Publication Date:** October 16, 2025
- **Document ID:** KSS-WP-20251016-CEV

## Abstract

This paper documents a proof-of-concept procedure for establishing immutable, verifiable records for the theoretical framework known as the Crown Equation. By applying the industry-standard SHA-256 cryptographic hashing algorithm to both numerical outputs and the symbolic representation of the equation, we demonstrate a method for ensuring data integrity and creating a foundational layer of trust for future applications. The procedure successfully generated unique and verifiable digests for three distinct cases, validating the process as a sound method for creating tamper-proof axiomatic identifiers within a larger system.

## 1. Introduction

In the design of any secure digital framework, the principles of integrity, verifiability, and non-repudiation are paramount. The ability to prove that a piece of data or a core formula has not been altered is the bedrock upon which complex systems are built. Cryptographic hashing functions, such as the Secure Hash Algorithm 256 (SHA-256), provide a robust mechanism for achieving this. A hash function converts an input of any size into a fixed-size string of characters, or "digest," which serves as a unique digital fingerprint.

The Crown Equation is a foundational component of a proprietary mathematical framework. To secure its core principles, it is necessary to establish a method for creating a permanent and verifiable record of its structure and outputs. This paper outlines the application of SHA-256 hashing to achieve this goal, creating verifiable proofs for specific instances of the Crown Equation.

## 2. Methodology

The procedure involved three stages of analysis, moving from a null-state calculation to a specific numerical instance, and finally to the symbolic representation of the formula itself.

### 2.1 The Crown Equation

The symbolic form of the equation under review is:

$$
\frac{AU_{256}}{\text{entropy} \times \text{decay}}
$$

where $AU_{256}$ represents a primary unit value.

### 2.2 Hashing Procedure

A three-step process was executed for each case:

1. **Define the input.** An expression was defined and its value calculated, or the symbolic string itself was used as the input.
2. **Generate the hash.** The resulting string (the "value/input string") was processed by the SHA-256 algorithm.
3. **Record the digest.** The resulting 64-character hexadecimal digest was recorded.

## 3. Results and Verification

Three distinct proofs were generated and verified. The input strings and their corresponding SHA-256 digests are presented below. Each hash was generated using UTF-8 encoded strings.

| Case | Expression | Value / Input String | SHA-256 Hash |
| --- | --- | --- | --- |
| 1. Null State | $0 / (\text{entropy} \times \text{decay})$ | `0/(entropy×decay)` | `c136cac1aa5600fa9ab9df86fdd45ee0b50d92f9eb6f03eb3c84451545c9feff` |
| 2. Instance | $\dfrac{256}{2 \times 2}$ | `256/(2×2)` | `48ffa98519e884c9a9387aa4ec1b462825d266826206077109a732206dacc6f7` |
| 3. Symbolic | $\dfrac{AU_{256}}{\text{entropy} \times \text{decay}}$ | `AU256/(entropy*decay)` | `6ea47f4818c29b431f61fc8970ed1e55b13036944083cb3f14ed9b67fcd2f706` |

Each hash was independently verified using Python's `hashlib` module. The following snippet reproduces the results:

```python
import hashlib

def sha256_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

cases = [
    "0/(entropy×decay)",
    "256/(2×2)",
    "AU256/(entropy*decay)",
]

for case in cases:
    print(case, sha256_digest(case))
```

Executing this script yields the digests shown in Table 1, demonstrating that the recorded hashes are reproducible and tamper-evident.

## 4. Discussion and Implications

The successful generation and verification of these hashes carry significant implications for the development of systems based on the Crown Equation.

- **Immutable record.** Each hash serves as a permanent, tamper-proof "seal." Any alteration to the input string, no matter how minor, would result in a completely different hash. This guarantees the integrity of the foundational data points.
- **Foundation for protocol design.** These verified hashes can now be used as axiomatic identifiers within smart contracts, data validation protocols, or secure communication systems. For example, a system could be designed to only accept transactions or data that can be proven to originate from these exact, hashed formulas.
- **Symbolic authentication.** Hashing the symbolic representation of the equation (Case 3) creates a digital fingerprint for the rule itself, not just its output. This allows for the authentication of the underlying logic of a system, ensuring that the correct formula is being used without having to execute it.

## 5. Conclusion

Applying the SHA-256 algorithm to the Crown Equation and its specific outputs has created a set of cryptographically secure, verifiable proofs that establish a foundation of integrity. These hashes serve as immutable cornerstones for the ongoing development of secure protocols and advanced digital frameworks built upon this mathematical system. The methodology is sound and provides a clear path for anchoring theoretical constructs to the deterministic world of cryptography.

## Appendix A: What Is a Cryptographic Hash?

A cryptographic hash is like a digital fingerprint. It is a mathematical algorithm that takes an input (such as a file, a message, or a simple string of text) and produces a unique, fixed-length string of characters. This fingerprint has a few key properties:

- **Deterministic.** The same input will always produce the exact same hash.
- **One-way.** It is practically impossible to reverse the process and figure out the original input from the hash.
- **Avalanche effect.** Changing even one tiny part of the input (like a single letter) will produce a completely different and unrecognizable hash.

These properties make hashes extremely useful for verifying data integrity—if the hash matches, the data is unchanged.
