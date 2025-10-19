import base64

import pytest

import hooded_crown_system as hcs


def test_hooded_crown_seal_is_deterministic(capsys):
    seal = hcs.HoodedCrownSeal("Operator").generate_seal()
    captured = capsys.readouterr().out
    assert "HOODED CROWN SEAL GENERATED" in captured
    assert seal == hcs.HoodedCrownSeal("Operator").generate_seal()
    decoded = base64.b64decode(seal.encode())
    assert len(decoded) == 32


def test_crown_khtx_encrypt_and_audit_are_consistent(capsys):
    khtx = hcs.CrownKHTX(operator_id=hcs.RUNTIME_ID, secret="secret")
    encrypted = khtx.encrypt("message")
    audit = khtx.audit_hash()
    out = capsys.readouterr().out
    assert "Encrypted Output" in out
    assert "Audit Hash" in out
    assert encrypted == hcs.CrownKHTX(operator_id=hcs.RUNTIME_ID, secret="secret").encrypt("message")
    assert len(audit) == 128


def test_genesis_omega_expression_matches_known_value():
    approx = hcs.genesis_omega_expression(segments=20_000)
    assert approx == pytest.approx(0.7726517, rel=1e-4)


def test_recursive_checksum_and_runtime_id():
    checksum = hcs.recursive_checksum("ARCHON_PRIME")
    assert len(checksum) == 64
    assert hcs.get_runtime_id() == "14104264743"
