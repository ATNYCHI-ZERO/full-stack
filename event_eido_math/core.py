r"""Core data structures and operations for the Event/Eido framework.

The implementation follows the formal definitions introduced in the
`docs/event_eido_math_formalization.md` whitepaper.  The module focuses on
constructs that can be evaluated numerically so that symbolic reasoning can be
validated through simulation and automated testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np
from numpy.typing import ArrayLike, NDArray


# ---------------------------------------------------------------------------
# Type aliases

Waveform = Callable[[float], NDArray[np.float64]]
RecursionFn = Callable[[float, NDArray[np.float64]], NDArray[np.float64]]


def _as_array(vector: ArrayLike) -> NDArray[np.float64]:
    """Convert ``vector`` to a floating point ``ndarray`` with copy semantics."""

    array = np.asarray(vector, dtype=float)
    if array.ndim == 0:
        array = array.reshape(1)
    return array.astype(float, copy=True)


# ---------------------------------------------------------------------------
# Event-math primitives


@dataclass
class EventNode:
    r"""Representation of an event in the Event Lattice.

    Parameters
    ----------
    birthpoint:
        Absolute time (or timestamp surrogate) used as origin for recursion.
    waveform:
        Time dependent signature that captures the phenomenological expression
        of the event.  ``waveform`` is assumed to map any real time to a vector
        in :math:`\mathbb{R}^n`.
    causal_vector:
        Vector encoding causal magnitude and direction within the lattice.
    recursion:
        Non-linear update rule governing the temporal evolution of the causal
        vector.
    hash_id:
        Stable identifier used to reference the node inside an
        :class:`EventLattice`.
    """

    birthpoint: float
    waveform: Waveform
    causal_vector: NDArray[np.float64]
    recursion: RecursionFn
    hash_id: str
    total_causal_vector: NDArray[np.float64] = field(default_factory=lambda: np.zeros(0))

    def sample_waveform(self, time: float) -> NDArray[np.float64]:
        r"""Evaluate the waveform at ``time``.

        The method is intentionally strict: returned values are copied to
        prevent in-place external modification which would violate the
        mathematical assumptions used in the formal model.
        """

        return np.array(self.waveform(time), dtype=float)

    def propagate(self, time: float) -> NDArray[np.float64]:
        r"""Evaluate the recursive transformation at ``time``.

        ``propagate`` encapsulates the recursive transformation function
        :math:`\mathcal{R}(t)` that appears in the Event-Math specification.
        """

        return np.array(self.recursion(time, self.causal_vector), dtype=float)

    def __post_init__(self) -> None:
        raw = _as_array(self.causal_vector)
        norm = np.linalg.norm(raw)
        causal = raw / norm if norm > 0 else raw
        if self.total_causal_vector.size == 0:
            total = np.array(raw, copy=True)
        else:
            total = _as_array(self.total_causal_vector)
        object.__setattr__(self, "causal_vector", causal)
        object.__setattr__(self, "total_causal_vector", total)


def combine_events(
    event_i: EventNode,
    event_j: EventNode,
    *,
    coupling_matrix: Optional[NDArray[np.float64]] = None,
    hash_id: Optional[str] = None,
) -> EventNode:
    r"""Combine two events using the :math:`\otimes_e` operator.

    The combined waveform is defined as the superposition of the input
    waveforms, optionally transformed by ``coupling_matrix``.  The causal
    vectors are added and then normalised to enforce numerical stability.

    Parameters
    ----------
    event_i, event_j:
        Input nodes.
    coupling_matrix:
        Optional linear transformation applied to the superposed waveform.
        When ``None`` a direct sum is used.
    hash_id:
        Identifier assigned to the resulting node.  When omitted an identifier
        is synthesised from the parents.
    """

    def combined_waveform(time: float) -> NDArray[np.float64]:
        wave = event_i.waveform(time) + event_j.waveform(time)
        wave = np.asarray(wave, dtype=float)
        if coupling_matrix is not None:
            wave = coupling_matrix @ wave
        return wave

    total_vector = event_i.total_causal_vector + event_j.total_causal_vector
    norm = np.linalg.norm(total_vector)
    combined_vector = total_vector / norm if norm > 0 else total_vector

    def combined_recursion(time: float, state: NDArray[np.float64]) -> NDArray[np.float64]:
        left = event_i.recursion(time, state)
        right = event_j.recursion(time, state)
        return 0.5 * (left + right)

    identifier = hash_id or f"{event_i.hash_id}⊗{event_j.hash_id}"
    birthpoint = min(event_i.birthpoint, event_j.birthpoint)

    return EventNode(
        birthpoint=birthpoint,
        waveform=combined_waveform,
        causal_vector=_as_array(combined_vector),
        recursion=combined_recursion,
        hash_id=identifier,
        total_causal_vector=_as_array(total_vector),
    )


def project_event(
    event: EventNode,
    delta_t: float,
    *,
    steps: int = 1,
) -> Tuple[float, NDArray[np.float64], NDArray[np.float64]]:
    r"""Propagate ``event`` forward using ``ℙₑ``.

    Returns
    -------
    Tuple consisting of the projected timestamp, the evolved causal state, and
    the waveform evaluated at the projected time.
    """

    time = event.birthpoint
    state = np.array(event.causal_vector, dtype=float)
    for _ in range(max(steps, 1)):
        time += delta_t
        state = event.recursion(time, state)
    waveform_value = event.waveform(time)
    return time, state, np.asarray(waveform_value, dtype=float)


def harmonic_time_vector(
    delta_t: float,
    waveform: Waveform,
    samples: Sequence[float] = (0.0, 0.25, 0.5, 0.75, 1.0),
) -> float:
    r"""Compute :math:`\Delta \mathcal{T}_e = \Delta t \times H(\mathcal{W})`.

    The harmonic weight :math:`H(\mathcal{W})` is approximated using the
    harmonic mean of waveform magnitudes at ``samples``.
    """

    magnitudes = []
    for sample in samples:
        value = np.linalg.norm(waveform(sample))
        magnitudes.append(max(value, 1e-12))
    harmonic_weight = len(magnitudes) / np.sum(1.0 / np.asarray(magnitudes))
    return float(delta_t * harmonic_weight)


@dataclass
class EventCollapseResult:
    r"""Container representing the result of an event collapse."""

    parent: EventNode
    branches: Tuple[EventNode, ...]


def collapse_event(
    event: EventNode,
    weights: Sequence[float],
    *,
    jitter: float = 0.0,
) -> EventCollapseResult:
    r"""Implement the ``⟡`` operator.

    ``weights`` defines how the causal vector is partitioned amongst the
    branches.  ``jitter`` can be used to introduce a bounded perturbation that
    models stochastic divergence.
    """

    weights_array = _as_array(weights)
    if np.any(weights_array < 0):
        raise ValueError("Collapse weights must be non-negative.")
    weight_sum = float(np.sum(weights_array))
    if weight_sum == 0:
        raise ValueError("At least one weight must be positive.")

    branches = []
    for idx, weight in enumerate(weights_array):
        branch_vector = (weight / weight_sum) * event.causal_vector

        def branch_waveform(time: float, *, _weight=weight) -> NDArray[np.float64]:
            base = event.waveform(time)
            perturbation = 0.0
            if jitter > 0:
                perturbation = np.random.default_rng().normal(scale=jitter, size=base.shape)
            return _weight * base + perturbation

        def branch_recursion(time: float, state: NDArray[np.float64], *, _weight=weight) -> NDArray[np.float64]:
            return _weight * event.recursion(time, state)

        branch = EventNode(
            birthpoint=event.birthpoint,
            waveform=branch_waveform,
            causal_vector=_as_array(branch_vector),
            recursion=branch_recursion,
            hash_id=f"{event.hash_id}:⟡{idx}",
            total_causal_vector=_as_array(branch_vector),
        )
        branches.append(branch)

    return EventCollapseResult(parent=event, branches=tuple(branches))


class EventLattice:
    r"""Mutable representation of the event lattice :math:`\mathcal{E}\Lambda`."""

    def __init__(self) -> None:
        self._nodes: Dict[str, EventNode] = {}
        self._edges: MutableMapping[str, set[str]] = {}

    def add_event(self, event: EventNode) -> None:
        self._nodes[event.hash_id] = event
        self._edges.setdefault(event.hash_id, set())

    def connect(self, source: str, target: str) -> None:
        if source not in self._nodes or target not in self._nodes:
            raise KeyError("Both source and target must exist in the lattice.")
        self._edges.setdefault(source, set()).add(target)

    def neighbours(self, node_id: str) -> Tuple[EventNode, ...]:
        return tuple(self._nodes[target] for target in self._edges.get(node_id, ()))

    def collapse(self, node_id: str, weights: Sequence[float]) -> EventCollapseResult:
        event = self._nodes[node_id]
        result = collapse_event(event, weights)
        for branch in result.branches:
            self.add_event(branch)
            self.connect(node_id, branch.hash_id)
        return result

    def __getitem__(self, node_id: str) -> EventNode:
        return self._nodes[node_id]

    def __contains__(self, node_id: str) -> bool:
        return node_id in self._nodes

    def items(self) -> Mapping[str, EventNode].items:
        return self._nodes.items()


# ---------------------------------------------------------------------------
# Glyph mapping


class Glyph(Enum):
    """Enumeration of glyphs used to annotate event resonance classes."""

    FIRE = "🜂"
    SHIELD = "⟁"
    EYE = "🧿"
    ATOM = "⚛"
    WAVE = "⌁"


def glyph_map(event: EventNode, samples: Sequence[float] = (0.0, 0.5, 1.0)) -> Glyph:
    """Map an event to a glyph using waveform entropy and causal intensity."""

    waveform_energy = np.mean([np.linalg.norm(event.waveform(sample)) for sample in samples])
    causal_norm = np.linalg.norm(event.causal_vector)

    if waveform_energy > 1.5 * causal_norm:
        return Glyph.WAVE
    if causal_norm > 1.5 * waveform_energy:
        return Glyph.SHIELD
    if waveform_energy > causal_norm:
        return Glyph.FIRE
    if causal_norm > waveform_energy:
        return Glyph.ATOM
    return Glyph.EYE


# ---------------------------------------------------------------------------
# Eido-math primitives


@dataclass
class EidoNode:
    """Representation of an ideal-form node."""

    archetypal_resonance: NDArray[np.float64]
    morphic_field: NDArray[np.float64]
    influence_vector: NDArray[np.float64]

    def normalise(self) -> "EidoNode":
        return EidoNode(
            archetypal_resonance=_normalise(self.archetypal_resonance),
            morphic_field=_normalise(self.morphic_field),
            influence_vector=_normalise(self.influence_vector),
        )


def _normalise(vector: NDArray[np.float64]) -> NDArray[np.float64]:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


@dataclass
class Recognition:
    """Result of the Eido recognition operator."""

    score: float
    residual: NDArray[np.float64]


class MorphicResolver:
    """Implements ``Φ``—the morphic resolver function."""

    def __init__(self, basis: NDArray[np.float64]) -> None:
        basis = np.asarray(basis, dtype=float)
        if basis.ndim != 2:
            raise ValueError("Basis must be a 2D matrix.")
        self._basis = basis

    def resolve(
        self,
        events: Sequence[EventNode],
        *,
        sampling_grid: Sequence[float] = (0.0, 0.5, 1.0),
    ) -> EidoNode:
        """Collapse a bundle of events into an Eido node."""

        if not events:
            raise ValueError("At least one event is required for resolution.")

        waveform_stack = []
        causal_stack = []
        for event in events:
            samples = [event.waveform(t) for t in sampling_grid]
            waveform_stack.append(np.mean(samples, axis=0))
            causal_stack.append(event.causal_vector)

        waveform_mean = np.mean(np.stack(waveform_stack, axis=0), axis=0)
        causal_mean = np.mean(np.stack(causal_stack, axis=0), axis=0)

        archetypal = self._basis @ waveform_mean
        morphic = self._basis @ causal_mean
        influence = waveform_mean + causal_mean

        return EidoNode(
            archetypal_resonance=archetypal,
            morphic_field=morphic,
            influence_vector=influence,
        )

    def recognise(self, event: EventNode, eido: EidoNode) -> Recognition:
        """Evaluate the recognition operator ``⊛``."""

        event_vector = np.concatenate((event.causal_vector, event.waveform(event.birthpoint)))
        form_vector = np.concatenate((eido.influence_vector, eido.archetypal_resonance))
        event_norm = np.linalg.norm(event_vector)
        form_norm = np.linalg.norm(form_vector)
        if event_norm == 0 or form_norm == 0:
            score = 0.0
        else:
            score = float(np.dot(event_vector, form_vector) / (event_norm * form_norm))

        projection = score * form_vector
        residual = event_vector - projection
        return Recognition(score=score, residual=residual)


def synthesize_eido(eido_a: EidoNode, eido_b: EidoNode, weight: float = 0.5) -> EidoNode:
    """Realise the ``⊞`` operator between two Eido nodes."""

    weight = float(np.clip(weight, 0.0, 1.0))
    complement = 1.0 - weight
    return EidoNode(
        archetypal_resonance=weight * eido_a.archetypal_resonance + complement * eido_b.archetypal_resonance,
        morphic_field=weight * eido_a.morphic_field + complement * eido_b.morphic_field,
        influence_vector=weight * eido_a.influence_vector + complement * eido_b.influence_vector,
    )


__all__ = [
    "EventNode",
    "EventLattice",
    "EventCollapseResult",
    "combine_events",
    "project_event",
    "collapse_event",
    "harmonic_time_vector",
    "Glyph",
    "glyph_map",
    "EidoNode",
    "MorphicResolver",
    "Recognition",
    "synthesize_eido",
]
