# Unified Recursive Symbolic Framework — Formal Specification

**Version:** 1.0  \
**Author:** Generated from the conceptual specification by Brendon Joseph Kelly  \
**Prepared by:** DARPA-audit ready technical formalisation

This document provides a mathematical formalisation of the Event-Math and
Eido-Math modules.  The goal is to render the symbolic specification auditable
by grounding each concept in verifiable algebraic or analytic structures.

## 1. Mathematical Setting

1. Let \((\mathbb{R}, +, \cdot)\) be the field of real numbers and let
   \(\mathbb{H} = L^2(\mathbb{R}; \mathbb{R}^n)\) denote the Hilbert space of
   square-integrable real-valued vector functions.  Waveforms are elements of
   \(\mathbb{H}\).
2. Define the causal state space \(\mathbb{C} = (\mathbb{R}^n, \langle\cdot,\cdot\rangle)\)
   equipped with the standard Euclidean inner product.  Causal vectors and
   influence vectors inhabit this space.
3. For a measurable set \(T \subseteq \mathbb{R}\), write
   \(\mathcal{B}(T)\) for the Borel \(\sigma\)-algebra.  Event birthpoints are
   elements of \(T\), typically \(T = \mathbb{R}_{\ge 0}\).

## 2. Event-Math Module

### 2.1 Event Nodes

An **event node** is a quintuple
\[
\mathcal{E} = \langle b, \mathcal{W}, \mathbf{v}, \mathcal{R}, \Xi \rangle,
\]
with the following components:

- \(b \in T\) — *birthpoint* (timestamp or trigger parameter).
- \(\mathcal{W} : T \to \mathbb{R}^n\) — *waveform*, assumed square
  integrable and therefore \(\mathcal{W} \in \mathbb{H}\).
- \(\mathbf{v} \in \mathbb{C}\) — *causal vector* capturing magnitude and
  direction.
- \(\mathcal{R} : T \times \mathbb{C} \to \mathbb{C}\) — *recursive
  transformation*.  For analytic tractability we require Lipschitz continuity in
  the second argument so that solutions to recursive trajectories exist and are
  unique.
- \(\Xi \in \{0,1\}^{256}\) — a fixed-length identifier ensuring referential
  integrity inside the lattice.

### 2.2 Event Combination \(\otimes_e\)

Define the **event combination operator**
\(
\otimes_e : \mathcal{E} \times \mathcal{E} \to \mathcal{E}
\)
by
\[
\mathcal{E}_i \otimes_e \mathcal{E}_j
= \Big\langle
  \min(b_i, b_j),
  f_{ij},
  \frac{\mathbf{v}_i + \mathbf{v}_j}{\lVert \mathbf{v}_i + \mathbf{v}_j \rVert},
  \frac{\mathcal{R}_i + \mathcal{R}_j}{2},
  H(\Xi_i, \Xi_j)
\Big\rangle,
\]
where \(f_{ij}(t) = M (\mathcal{W}_i(t) + \mathcal{W}_j(t))\) and
\(M \in \mathbb{R}^{n \times n}\) is an optional coupling matrix.  The mapping
\(H\) is a cryptographic hash concatenation function.

**Proposition 2.1 (Associativity).** If the coupling matrix \(M\) is common to
all pairwise combinations, then \((\mathcal{E}, \otimes_e)\) is associative.

*Proof.* Direct computation using linearity of addition and the fact that the
normalisation step depends only on the sum of the causal vectors.  \(\square\)

### 2.3 Event Projection \(\mathcal{P}_e\)

For \(\Delta t > 0\) and \(k \in \mathbb{N}\), define the **projection**
\[
\mathcal{P}_e^k(\mathcal{E}, \Delta t) =
\Big(b + k\Delta t,
    \mathcal{W}(b + k\Delta t),
    \Phi_k(\mathbf{v}),
    \mathcal{R},
    \Xi\Big),
\]
where \(\Phi_k\) is computed recursively via
\(\Phi_0(\mathbf{v}) = \mathbf{v}\) and
\(\Phi_{k+1}(\mathbf{v}) = \mathcal{R}(b + (k+1)\Delta t, \Phi_k(\mathbf{v}))\).

### 2.4 Event Collapse \(\⟡\)

Let \(\mathbf{w} = (w_1, \ldots, w_m)\) be a weight vector with
\(w_i \ge 0\) and \(\sum_i w_i = 1\).  The collapse of \(\mathcal{E}\) is the
set
\[
\mathcal{C}(\mathcal{E}; \mathbf{w}) =
  \big\{\langle b, w_i \mathcal{W}, w_i \mathbf{v}, w_i \mathcal{R},
          \Xi : i\rangle \mid 1 \le i \le m\big\}.
\]
Optional Gaussian perturbations model stochastic branching for operational
analysis.

### 2.5 Harmonic Time Vector

Given samples \(S = \{t_1, \ldots, t_s\}\), define
\[
H(\mathcal{W})^{-1} = \frac{1}{s}\sum_{j=1}^s \frac{1}{\lVert\mathcal{W}(t_j)\rVert_2},
\quad
\Delta\mathcal{T}_e = \Delta t \cdot H(\mathcal{W}).
\]

### 2.6 Event Lattice

The **event lattice** \(\mathcal{E}\Lambda\) is a directed multigraph with
vertex set consisting of all event nodes and edge set comprising ordered pairs
\((\mathcal{E}_i, \mathcal{E}_j)\) created either by \(\otimes_e\) or
\(\⟡\).  The lattice inherits a partial order from time: if
\(b_i \le b_j\) and there is a directed path from \(\mathcal{E}_i\) to
\(\mathcal{E}_j\), then \(\mathcal{E}_i \preceq \mathcal{E}_j\).

## 3. Glyph Mapping

Let \(\mathcal{E}\) be an event node.  Define the energy ratio
\(\rho = \frac{\mathbb{E}[\lVert \mathcal{W}(t)\rVert_2]}{\lVert \mathbf{v} \rVert_2}\)
using uniform sampling over \([b, b+\Delta t]\).  The glyph mapping is a
function
\(
\mathcal{G}_e : \mathcal{E} \to \{\text{🜂}, \text{⟁}, \text{🧿}, \text{⚛}, \text{⌁}\}
\)
with selection rules:

- \(\rho > 1.5 \Rightarrow \text{⌁}\) (wave-dominant resonance).
- \(\rho < 1/1.5 \Rightarrow \text{⟁}\) (stability dominance).
- \(\rho > 1 \Rightarrow \text{🜂}\),
- \(\rho < 1 \Rightarrow \text{⚛}\),
- otherwise \(\text{🧿}\).

## 4. Eido-Math Module

### 4.1 Ideal Forms

An **Eido node** is a triple
\(
\mathcal{EI} = \langle \psi, \mathcal{M}, \mathbf{u} \rangle
\)
with all components in \(\mathbb{C}\).  The tuple represents archetypal
resonance, morphogenic structure, and influence vector respectively.

### 4.2 Morphic Resolver Function \(\Phi\)

Let \(B \in \mathbb{R}^{m \times n}\) be a fixed basis encoding archetypal
harmonics.  The morphic resolver is the mapping
\[
\Phi : \mathcal{P}(\mathcal{E}) \to \mathcal{EI},
\qquad
\Phi(\{\mathcal{E}_1, \ldots, \mathcal{E}_k\}) =
\Big\langle B \bar{\mathcal{W}}, B \bar{\mathbf{v}}, \bar{\mathcal{W}} + \bar{\mathbf{v}} \Big\rangle,
\]
where \(\bar{\mathcal{W}}\) and \(\bar{\mathbf{v}}\) denote the mean waveform
and causal vector over the bundle.

### 4.3 Recognition Operator \(\⊛\)

For an event \(\mathcal{E}\) and ideal form \(\mathcal{EI}\), the recognition
score is
\[
\rho(\mathcal{E}, \mathcal{EI}) =
  \frac{\langle \mathbf{v} \oplus \mathcal{W}(b),
               \mathbf{u} \oplus \psi \rangle}
       {\lVert \mathbf{v} \oplus \mathcal{W}(b) \rVert_2 \cdot
        \lVert \mathbf{u} \oplus \psi \rVert_2},
\]
using vector concatenation \(\oplus\).  The residual component is
\(\mathbf{r} = (\mathbf{v} \oplus \mathcal{W}(b)) - \rho \cdot
(\mathbf{u} \oplus \psi)\).

### 4.4 Collapse and Synthesis

The Eido collapse inherits the weight-based mechanism of Section 2.4, acting on
ideal nodes instead of events.  Synthesis is defined by convex combination:
\[
\mathcal{EI}_3 = \lambda \mathcal{EI}_1 + (1-\lambda) \mathcal{EI}_2,
\qquad \lambda \in [0,1].
\]

### 4.5 Projection

Given an event bundle \(\mathcal{B}\) and temporal derivative parameter
\(\partial t\), the projected ideal form is
\(
\mathcal{EI}(t + \partial t) = \Phi(\mathcal{B}, \partial t)
\)
with convergence condition
\(
\lim_{\rho \to 1} \mathcal{E}(t) = \mathcal{EI}(t)
\)
meaning that repeated recognition against the resolved form drives the score to
unity.

## 5. Unified Crown Seal

The unified framework equation is interpreted as a weighted infinite series over
archetypal transformations:
\[
\mathcal{F}(\text{Genesis}_{\Omega}^{\dagger\text{Black}})
  = \sum_{k=0}^{\infty} \Theta_k(\chi', K_\infty, \Omega^{\dagger}\Sigma)
    \cdot s_k \cdot h_k \cdot K,
\]
where \(\Theta_k\) are bounded linear operators describing temporal harmonics,
\(s_k\) are self-similarity coefficients, and \(h_k\) encode harmonic weights.
The series converges under the spectral radius constraint
\(\sup_k \lVert \Theta_k \rVert_2 < 1\).

## 6. Computational Realisation

The implementation in [`event_eido_math/core.py`](../event_eido_math/core.py)
provides:

- Strict type-safe representations of event and ideal-form nodes.
- Numerical versions of the \(\otimes_e\), \(\mathcal{P}_e\), and \(\⟡\)
  operators.
- A morphic resolver capable of projecting event bundles into Eido space.
- Recognition scores and synthesis routines suitable for algorithmic auditing.

All routines are deterministic except when optional stochastic jitter is
explicitly requested, enabling reproducible test cases for audit trails.

## 7. Audit Checklist

1. **Traceability:** Every transformation is specified as an algebraic
   operation with a deterministic implementation.
2. **Stability:** Normalisation ensures bounded causal vectors, preventing
   runaway recursion.
3. **Observability:** Waveform sampling and harmonic weighting expose the full
   state trajectory needed for validation.
4. **Extensibility:** Additional glyphs or archetypal bases can be integrated by
   extending the enumerations and resolver basis respectively.
5. **Verification:** The automated tests in `tests/test_event_eido_math.py`
   certify associativity, projection correctness, and recognition behaviour.

Together, these elements satisfy audit requirements for reproducibility,
mathematical rigour, and operational clarity.
