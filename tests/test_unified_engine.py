"""Integration smoke-test for the :mod:`crown_unified_engine` module."""

from crown_unified_engine import CrownUnifiedEngine, UnifiedEngineReport


def test_unified_engine_round_trip() -> None:
    engine = CrownUnifiedEngine()
    report = engine.run()

    assert isinstance(report, UnifiedEngineReport)

    # Handshake output should decrypt to the configured message.
    assert report.handshake.decrypted_plaintext == engine.config.message
    assert len(report.handshake.shared_secret_digest) == 64

    # Process artefacts should match the underlying system dimensions.
    discretisation = report.process.discretisation
    assert discretisation.phi.shape == engine.config.matrix_a.shape
    assert discretisation.gamma.shape[0] == engine.config.matrix_a.shape[0]
    assert report.process.math_salt

    # Ω summaries must respect the signal dimensionality.
    assert report.omega.signal.shape == report.omega.omega_signal.shape
    assert report.omega.displaced_signal.shape == report.omega.signal.shape
    assert isinstance(report.omega.zeta_shadow, complex)

    # Hooded Crown harness should produce artefacts.
    assert report.hooded.seal
    assert report.hooded.encrypted_payload
    assert report.hooded.audit_hash
    assert isinstance(report.hooded.genesis_integral, float)

