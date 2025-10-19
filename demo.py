"""Demonstration harness for the intent-auth encryption envelope."""
from __future__ import annotations

import json
from typing import Any

import numpy as np
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from audit_log import AuditLog
from crypto_core import KEMStub, derive_key, encrypt_message, decrypt_message
from intent_model import IntentModel
from policy_engine import Policy, decide


def _log_event(audit: AuditLog, action: str, **details: Any) -> None:
    payload = {"action": action}
    payload.update(details)
    audit.log(payload)


def demo() -> None:
    print("POC demo start")
    receiver_sk = X25519PrivateKey.generate()
    receiver_pk = receiver_sk.public_key()

    signer = Ed25519PrivateKey.generate()
    audit = AuditLog(signer)

    operator_fp = "K-MATH::Ωv1".encode("utf-8")
    policy = Policy()

    # encapsulate session key
    encapsulated, shared_secret = KEMStub.encapsulate(receiver_pk)
    sym_key = derive_key(shared_secret, operator_fp)
    package = encrypt_message(
        b"SECRET: The quick brown fox.",
        sym_key,
        associated_data=json.dumps({"policy_id": policy.policy_id}).encode("utf-8"),
    )
    _log_event(audit, "encrypt", policy_id=policy.policy_id, encapsulation=encapsulated.hex())
    print("Ciphertext generated")

    model = IntentModel()
    model.train()

    benign_features = np.array([0.58, 0.39, 0.68, 0.18, 0.25, 0.52])
    score, explanation = model.predict(benign_features)
    decision = decide(score, policy)
    _log_event(audit, "decision", score=score, decision=decision, explanation=explanation)
    print("Benign score", score, "->", decision)

    if decision == "ALLOW":
        shared2 = KEMStub.decapsulate(receiver_sk, encapsulated)
        sym2 = derive_key(shared2, operator_fp)
        plaintext = decrypt_message(
            package.ciphertext,
            package.nonce,
            sym2,
            associated_data=json.dumps({"policy_id": policy.policy_id}).encode("utf-8"),
        )
        print("Decrypted plaintext:", plaintext)
    else:
        print("Access denied")

    malicious_features = np.array([0.28, 0.72, 0.32, 0.62, 0.78, 0.18])
    score2, explanation2 = model.predict(malicious_features)
    decision2 = decide(score2, policy)
    _log_event(audit, "decision", score=score2, decision=decision2, explanation=explanation2)
    print("Malicious score", score2, "->", decision2)


if __name__ == "__main__":
    demo()
