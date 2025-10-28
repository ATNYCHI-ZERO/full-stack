# Peer Review of "Breaking SHA-256 Using Crown Omega Mathematics"

**Reviewer:** Gemini AI Assistant (acting as peer reviewer)  
**Author:** Brendon Joseph Kelly  
**Date:** August 7, 2025  

## Summary

The manuscript introduces a speculative framework called *Crown Omega Mathematics* and claims it enables efficient attacks on the SHA-256 hash function. The proposed toolkit comprises three novel constructs—Omega Reduction, Kharnita Matrices, and Atnychi Functions—whose interaction purportedly simplifies the SHA-256 compression function enough to permit second pre-image attacks against reduced-round variants (up to 12 rounds, according to the author).

The paper is written in a conventional scientific format and the argument flows logically. Nevertheless, the claims rest on concepts that are neither defined with mathematical rigor nor grounded in the cryptographic literature, leaving the results unverifiable.

## Major Comments

### 1. Undefined theoretical primitives

* **Omega Reduction** is illustrated through routine polynomial factorization. To demonstrate novelty, the manuscript must present a formal definition of the operator, including its domain, codomain, and algebraic properties, and then show how it applies to bitwise and modular operations that govern SHA-256.
* **Kharnita Matrices** are asserted to encode SHA-256 rounds and to commute under multiplication. Because SHA-256 round transformations are non-commutative, the manuscript must provide construction rules, explicit examples, and a formal proof of the claimed associativity/commutativity.
* **Atnychi Functions** are described as infinite series modeling SHA-256 state evolution. The author needs to justify why an analytic representation is appropriate for a finite-state, discrete system, and to demonstrate how the series enables symbolic cancellation of SHA-256’s nonlinear mixing.

Without precise definitions, the framework is metaphorical rather than mathematical.

### 2. Application to SHA-256 lacks reproducibility

* The manuscript asserts that the 64 SHA-256 rounds can be "simplified into a tractable polynomial representation." A detailed derivation for at least one full round—covering message schedule, state update, and constants—is essential to substantiate this claim.
* The reported second pre-image findings for 8–12 round SHA-256 need supporting evidence. The paper should include explicit colliding input pairs and publish the referenced Python/SageMath tooling so the community can reproduce the experiments.

### 3. Overstated implications

Even if the reduced-round claims were validated, generalizing the result to full SHA-256 remains speculative. The conclusion should temper its language until the theory is rigorously developed and independent verifications are available.

## Recommendation

**Reject (encourage major revision).**

To progress toward publishable work, the author should:

1. Provide textbook-level formal definitions and proofs for all new constructs.
2. Work through a complete SHA-256 round using the proposed machinery, step by step.
3. Release the experimental framework and furnish concrete collision examples for the reduced-round settings.
4. Situate the approach within established cryptanalytic techniques (algebraic, differential, linear, etc.) to clarify its novelty.

The concepts are intriguing, but substantial foundational work is required before the manuscript can meet the standards of the cryptographic research community.
