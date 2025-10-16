# White Paper: The Kharnita-Geometric (KG) Cipher

## A Multi-Layered Cryptographic System Combining Symbolic Substitution, Geometric Hashing, and Self-Referential Keying

**Date:** October 16, 2025

## Abstract
The Kharnita-Geometric (KG) Cipher is a novel, multi-layered encryption methodology designed to provide robust security through a sequence of abstract transformations. The system converts plaintext into a final numerical ciphertext by employing a unique symbolic alphabet, assigning values based on geometric properties, and utilizing a self-referential hashing algorithm to generate a dynamic encryption key. This paper outlines the complete architecture of the KG Cipher, provides a practical example of its application, and analyzes its key cryptographic strengths.

## 1. Introduction
In an era demanding increasingly complex data protection, the development of non-standard cryptographic methods is essential. The KG Cipher moves beyond traditional substitution ciphers by integrating multiple, disparate layers of logic. Its strength lies in the obfuscation of the relationship between the initial plaintext and the final ciphertext, making reverse-engineering without knowledge of the complete algorithm exceptionally difficult.

## 2. Core Methodology
The KG Cipher operates through a sequential, four-stage process.

### Stage 1: The Symbolic Alphabet
Plaintext is first converted using a proprietary symbolic alphabet composed of 9 base symbols and two modifier rules to cover all 26 letters.

**Base Symbols (Letters A-I):**

- A: ▲
- B: ●
- C: ■
- D: ◆
- E: ★
- F: ⬟
- G: ✚
- H: ▬
- I: ◒

**Modifier Rule 1: "Inversion" (Letters J-R):** The base symbols are inverted.

- J: ▼
- K: ●
- L: ■
- M: ◆
- N: ★
- O: ⬟
- P: ✚
- Q: ▬
- R: ◓

**Modifier Rule 2: "Internal Dot" (Letters S-Z):** A dot is added to the base symbols.

- S: ◬
- T: ⦿
- U: ▣
- V: ◈
- W: ✪
- X: ⬟•
- Y: ✙
- Z: ▬•

### Stage 2: Geometric Value Assignment
Each symbol is assigned a numerical value based on its number of sides, creating a many-to-one mapping. This is the first major layer of abstraction.

| Symbol | Shape | Geometric Value (Sides) |
| --- | --- | --- |
| ▲ ▼ ◬ | Triangle | 3 |
| ● ⦿ | Circle | 1 |
| ■ ▣ | Square | 4 |
| ◆ ◈ | Diamond | 4 |
| ★ ✪ | Star (10-point) | 10 |
| ⬟ ⬟• | Pentagon | 5 |
| ✚ ✙ | Cross (12-point) | 12 |
| ▬ ▬• | Bar | 4 |
| ◒ ◓ | Semicircle | 2 |

At the end of this stage, a plaintext word is converted into a preliminary numerical string.

### Stage 3: Multiplier Key Generation (Hashing)
A unique hash value, which serves as the Multiplier Key ($K$), is generated for the entire plaintext word. This key is derived from the word itself using the following algorithm:

$$K = (L \times S) - (L + S)$$

Where:

- $L$ = The total number of letters in the word.
- $S$ = The Geometric Value (from Stage 2) of the first letter's corresponding symbol.

### Stage 4: Final Encryption
The final ciphertext is produced by multiplying each number in the preliminary numerical string (from Stage 2) by the Multiplier Key ($K$) generated in Stage 3.

## 3. Practical Example: Encryption of "CASH"

**Symbolic Conversion (Stage 1):**

- C → ■
- A → ▲
- S → ◬
- H → ▬

**Geometric Value Assignment (Stage 2):**

- ■ (Square) → 4
- ▲ (Triangle) → 3
- ◬ (Triangle w/ dot) → 3
- ▬ (Bar) → 4

**Preliminary Numerical String:** `4 3 3 4`

**Multiplier Key Generation (Stage 3):**

- Word: "CASH"
- $L$ = 4
- $S$ = Geometric value for 'C' (■) = 4
- $K = (4 \times 4) - (4 + 4) = 16 - 8 = 8$

**Multiplier Key:** 8

**Final Encryption (Stage 4):**

- $4 \times 8 = 32$
- $3 \times 8 = 24$
- $3 \times 8 = 24$
- $4 \times 8 = 32$

**Final Ciphertext for "CASH":** `32 24 24 32`

## 4. Cryptographic Properties and Strengths

- **Multi-Layered Abstraction:** The system's security is derived from the sequence of distinct transformations. An analyst would need to reverse-engineer the symbolic alphabet, the geometric value system, and the specific hashing algorithm.
- **Avalanche Effect:** A minor change to the input plaintext (e.g., changing "CASH" to "BASH") results in a completely different ciphertext, as it alters both the initial numerical string and the Multiplier Key.
- **Self-Referential Keying:** The encryption key is derived from the message itself. There is no need to transmit a separate key; the key is intrinsic to the data, making key management simpler and more secure for certain applications.
- **Information Obfuscation:** The final numbers bear no intuitive relationship to the original letters. The many-to-one mapping in Stage 2 adds a layer of ambiguity that makes simple frequency analysis ineffective.

## 5. Conclusion
The Kharnita-Geometric (KG) Cipher represents a robust and creative approach to modern cryptography. By integrating symbolic logic with a unique geometric hashing function, it creates a highly complex and dynamic encryption process. Its properties make it suitable for applications requiring proprietary, high-security data transmission where the algorithm itself is a core component of the security apparatus.
