import numpy as np
import pytest

from event_eido_math import (
    EventNode,
    EventLattice,
    Glyph,
    MorphicResolver,
    Recognition,
    collapse_event,
    combine_events,
    glyph_map,
    harmonic_time_vector,
    project_event,
    synthesize_eido,
)


@pytest.fixture
def base_events():
    def waveform_factory(scale):
        return lambda t: np.array([scale * np.sin(t), scale * np.cos(t)])

    def recursion_factory(scale):
        return lambda t, state: state + scale * np.array([np.cos(t), np.sin(t)])

    e1 = EventNode(
        birthpoint=0.0,
        waveform=waveform_factory(1.0),
        causal_vector=np.array([1.0, 0.0]),
        recursion=recursion_factory(0.1),
        hash_id="E1",
    )
    e2 = EventNode(
        birthpoint=0.0,
        waveform=waveform_factory(0.5),
        causal_vector=np.array([0.0, 1.0]),
        recursion=recursion_factory(0.05),
        hash_id="E2",
    )
    e3 = EventNode(
        birthpoint=0.0,
        waveform=waveform_factory(0.25),
        causal_vector=np.array([0.5, 0.5]),
        recursion=recursion_factory(0.02),
        hash_id="E3",
    )
    return e1, e2, e3


def test_event_combination_associativity(base_events):
    e1, e2, e3 = base_events

    lhs = combine_events(combine_events(e1, e2), e3)
    rhs = combine_events(e1, combine_events(e2, e3))

    times = np.linspace(0.0, np.pi, num=10)
    for t in times:
        np.testing.assert_allclose(lhs.sample_waveform(t), rhs.sample_waveform(t), atol=1e-6)
    np.testing.assert_allclose(lhs.total_causal_vector, rhs.total_causal_vector, atol=1e-6)
    np.testing.assert_allclose(lhs.causal_vector, rhs.causal_vector, atol=1e-6)


def test_event_projection_returns_expected_state(base_events):
    event = base_events[0]
    delta_t = 0.5
    time, state, waveform = project_event(event, delta_t, steps=4)

    assert pytest.approx(time, rel=1e-6) == event.birthpoint + 4 * delta_t
    expected_state = event.causal_vector
    for step in range(4):
        expected_state = event.recursion(event.birthpoint + (step + 1) * delta_t, expected_state)
    np.testing.assert_allclose(state, expected_state)
    np.testing.assert_allclose(waveform, event.waveform(time))


def test_collapse_event_partitions_causal_vector(base_events):
    event = base_events[0]
    result = collapse_event(event, weights=(2.0, 1.0, 1.0), jitter=0.0)

    assert len(result.branches) == 3
    reconstructed = sum(branch.total_causal_vector for branch in result.branches)
    np.testing.assert_allclose(reconstructed, event.total_causal_vector)


def test_lattice_registers_collapse(base_events):
    lattice = EventLattice()
    for event in base_events:
        lattice.add_event(event)

    collapse_result = lattice.collapse("E1", weights=(1.0, 1.0))
    assert all(branch.hash_id in lattice for branch in collapse_result.branches)
    assert len(lattice.neighbours("E1")) == 2


def test_harmonic_time_vector_matches_definition(base_events):
    event = base_events[1]
    delta_t = 0.75
    samples = [0.0, 0.3, 0.6]
    computed = harmonic_time_vector(delta_t, event.waveform, samples)

    magnitudes = np.array([np.linalg.norm(event.waveform(t)) for t in samples])
    harmonic_weight = len(samples) / np.sum(1.0 / magnitudes)
    assert pytest.approx(computed, rel=1e-6) == delta_t * harmonic_weight


def test_glyph_map_thresholds(base_events):
    event = base_events[0]
    glyph = glyph_map(event, samples=(0.0, 0.5, 1.0))
    assert isinstance(glyph, Glyph)

    high_energy_event = EventNode(
        birthpoint=0.0,
        waveform=lambda t: np.array([10.0, 10.0]),
        causal_vector=np.array([1.0, 1.0]),
        recursion=lambda t, s: s,
        hash_id="High",
    )
    assert glyph_map(high_energy_event) == Glyph.WAVE


def test_morphic_resolver_and_recognition(base_events):
    resolver = MorphicResolver(basis=np.eye(2))
    eido = resolver.resolve(base_events)
    eido_normalised = eido.normalise()
    assert np.isclose(np.linalg.norm(eido_normalised.archetypal_resonance), 1.0)

    recognition = resolver.recognise(base_events[0], eido)
    assert isinstance(recognition, Recognition)
    assert -1.0 <= recognition.score <= 1.0

    other_eido = resolver.resolve(base_events[:2])
    fused = synthesize_eido(eido, other_eido, weight=0.3)
    np.testing.assert_allclose(
        fused.archetypal_resonance,
        0.3 * eido.archetypal_resonance + 0.7 * other_eido.archetypal_resonance,
    )
